import logging
import asyncio
from datetime import datetime, timezone
from app.schemas.sensor_snapshot import SensorSnapshot
from app.schemas.fused_state import FusedState, OrientationState, MotionState, ObstacleState, LineStateOut, TiltState, ImpactState
from app.services.cache_service import cache_service
from app.services.event_service import event_service
from app.services.kafka_service import kafka_service
from app.services.websocket_service import websocket_service
from app.config.settings import settings
from app.filters import ultrasonic, imu, line_sensor, freshness
from app.fusion import obstacle, motion, orientation, health, confidence

logger = logging.getLogger(__name__)

class FusionService:
    def __init__(self):
        # Prevent tight loop processing by debouncing publishes per robot
        self.last_publish: dict = {}

    async def process_snapshot(self, snapshot: SensorSnapshot):
        robot_id = snapshot.robot_id
        current_time = datetime.now(timezone.utc)
        
        # Extract snapshot time
        occurred_at = snapshot.occurred_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        # Check sequence freshness
        latest_seq = await cache_service.get_latest_sequence(robot_id)
        if snapshot.sequence < latest_seq:
            # Check for large drop indicating restart
            if latest_seq - snapshot.sequence > 1000:
                logger.info(f"Robot {robot_id} sequence reset detected")
            else:
                logger.debug(f"Stale sequence {snapshot.sequence} for {robot_id}, latest is {latest_seq}")
                return
                
        await cache_service.update_latest_sequence(robot_id, snapshot.sequence)
        
        # Load previous states
        prev_state_dict = await cache_service.get_latest_fused_state(robot_id)
        
        # 1. Ultrasonic Processing
        obstacle_state = self._default_obstacle()
        if snapshot.sensors and snapshot.sensors.ultrasonic:
            await cache_service.update_last_seen(robot_id, "ultrasonic", occurred_at.isoformat())
            
            raw_d = snapshot.sensors.ultrasonic.distance_cm
            angle = snapshot.sensors.ultrasonic.scan_angle_deg
            direction = ultrasonic.get_scan_direction(angle)
            
            samples = await cache_service.get_sensor_samples(robot_id, "ultrasonic", direction)
            prev_ema = prev_state_dict["obstacle"]["distance_cm"] if prev_state_dict and prev_state_dict.get("obstacle", {}).get("direction") == direction else None
            
            filtered_d, new_samples = ultrasonic.filter_ultrasonic_distance(raw_d, samples, prev_ema)
            await cache_service.save_sensor_samples(robot_id, "ultrasonic", new_samples, direction)
            
            if filtered_d is not None:
                risk = obstacle.estimate_obstacle_risk(filtered_d)
                obstacle_state = ObstacleState(
                    detected=risk != "NONE",
                    direction=direction,
                    distance_cm=filtered_d,
                    risk_level=risk,
                    confidence=0.9
                )
                
                # Check transitions
                if prev_state_dict:
                    prev_risk = prev_state_dict.get("obstacle", {}).get("risk_level", "NONE")
                    if risk != "NONE" and prev_risk == "NONE":
                        await event_service.publish_and_store_event(robot_id, "OBSTACLE_DETECTED", "WARNING", 0.9, {"distance": filtered_d})
                    elif risk == "NONE" and prev_risk != "NONE":
                        await event_service.publish_and_store_event(robot_id, "OBSTACLE_CLEARED", "INFO", 0.9, {})

        # 2. IMU Processing
        orientation_state = self._default_orientation()
        tilt_state = self._default_tilt()
        impact_state = self._default_impact()
        is_moving_accel = False
        
        if snapshot.sensors and snapshot.sensors.imu:
            await cache_service.update_last_seen(robot_id, "imu", occurred_at.isoformat())
            imu_data = snapshot.sensors.imu
            
            # Simple low pass for accel
            prev_ax = prev_state_dict["_internal"]["ax"] if prev_state_dict and "_internal" in prev_state_dict else None
            prev_ay = prev_state_dict["_internal"]["ay"] if prev_state_dict and "_internal" in prev_state_dict else None
            prev_az = prev_state_dict["_internal"]["az"] if prev_state_dict and "_internal" in prev_state_dict else None
            
            ax = imu.low_pass_filter(imu_data.acceleration_x, prev_ax)
            ay = imu.low_pass_filter(imu_data.acceleration_y, prev_ay)
            az = imu.low_pass_filter(imu_data.acceleration_z, prev_az)
            
            # Pitch and roll filtering (simplified, assume raw is OK if no dt tracking)
            # Normalizing heading
            heading = imu.normalize_heading(imu_data.heading_deg)
            
            orientation_state = OrientationState(
                heading_deg=heading,
                pitch_deg=imu_data.pitch_deg,
                roll_deg=imu_data.roll_deg,
                confidence=0.85
            )
            
            unsafe_tilt = orientation.is_tilt_unsafe(imu_data.pitch_deg, imu_data.roll_deg)
            tilt_state = TiltState(unsafe=unsafe_tilt, confidence=0.9)
            if unsafe_tilt and prev_state_dict and not prev_state_dict.get("tilt", {}).get("unsafe"):
                await event_service.publish_and_store_event(robot_id, "UNSAFE_TILT", "CRITICAL", 0.9, {})

            impact = orientation.detect_possible_impact(ax, ay, az)
            impact_state = ImpactState(possible=impact, confidence=0.85)
            if impact and prev_state_dict and not prev_state_dict.get("impact", {}).get("possible"):
                await event_service.publish_and_store_event(robot_id, "POSSIBLE_IMPACT", "CRITICAL", 0.85, {})
                
            is_moving_accel = abs(ax) > 0.5 or abs(ay) > 0.5 # Simple heuristic

        # 3. Line Sensor Processing
        line_state = self._default_line()
        if snapshot.sensors and snapshot.sensors.line:
            await cache_service.update_last_seen(robot_id, "line_sensor", occurred_at.isoformat())
            
            # Simplified line state without history for brevity in this initial implementation
            curr_state_dict = snapshot.sensors.line.model_dump()
            
            err = line_sensor.calculate_normalized_error(curr_state_dict)
            pos = line_sensor.get_line_position(curr_state_dict)
            
            line_state = LineStateOut(
                detected=pos != "LOST",
                position=pos,
                normalized_error=err,
                confidence=0.9
            )
            
            if prev_state_dict:
                prev_pos = prev_state_dict.get("line", {}).get("position", "LOST")
                if pos == "LOST" and prev_pos != "LOST":
                    await event_service.publish_and_store_event(robot_id, "LINE_LOST", "WARNING", 0.9, {})
                elif pos != "LOST" and prev_pos == "LOST":
                    await event_service.publish_and_store_event(robot_id, "LINE_RECOVERED", "INFO", 0.9, {})

        # 4. Motion State
        motion_state = self._default_motion()
        if snapshot.robot_state:
            await cache_service.update_last_seen(robot_id, "robot_state", occurred_at.isoformat())
            rs = snapshot.robot_state
            
            m_state = motion.get_motion_state(rs.commanded_direction, rs.commanded_speed, rs.motor_active, is_moving_accel)
            possible_stall = motion.detect_possible_stall(rs.commanded_speed, rs.motor_active, is_moving_accel)
            
            motion_state = MotionState(
                state=m_state,
                confidence=0.8,
                possible_stall=possible_stall
            )
            
            if possible_stall and prev_state_dict and not prev_state_dict.get("motion", {}).get("possible_stall"):
                await event_service.publish_and_store_event(robot_id, "POSSIBLE_STALL", "WARNING", 0.8, {})

        # 5. Freshness & Health
        health_dict = {}
        for s_type in ["ultrasonic", "imu", "line_sensor", "vision"]:
            last_seen_str = await cache_service.get_last_seen(robot_id, s_type)
            fresh = "UNAVAILABLE"
            if last_seen_str:
                last_seen_dt = datetime.fromisoformat(last_seen_str)
                fresh = freshness.calculate_freshness(last_seen_dt, current_time)
            
            st = health.evaluate_sensor_health(fresh, 0, 0) # simplified
            health_dict[s_type] = st.value

        # 6. Overall Confidence
        avg_conf = confidence.calculate_confidence("FRESH", "HEALTHY")

        # Combine
        fused = FusedState(
            robot_id=robot_id,
            timestamp=current_time,
            sequence=snapshot.sequence,
            orientation=orientation_state,
            motion=motion_state,
            obstacle=obstacle_state,
            line=line_state,
            tilt=tilt_state,
            impact=impact_state,
            sensor_health=health_dict,
            overall_confidence=avg_conf
        )
        
        # Save and Publish
        state_dict = fused.model_dump()
        
        # Retain internal state for next iteration
        state_dict["_internal"] = {
            "ax": snapshot.sensors.imu.acceleration_x if snapshot.sensors and snapshot.sensors.imu else 0,
            "ay": snapshot.sensors.imu.acceleration_y if snapshot.sensors and snapshot.sensors.imu else 0,
            "az": snapshot.sensors.imu.acceleration_z if snapshot.sensors and snapshot.sensors.imu else 0,
        }
        
        # Convert datetime for JSON serialization
        state_dict["timestamp"] = state_dict["timestamp"].isoformat()
        
        await cache_service.save_latest_fused_state(robot_id, state_dict)
        
        # Throttle Kafka/WS publish to avoid spam (e.g. 5Hz)
        now = asyncio.get_event_loop().time()
        if robot_id not in self.last_publish or (now - self.last_publish[robot_id]) > (1.0 / settings.FUSION_OUTPUT_RATE_HZ):
            await kafka_service.publish_fused_state(state_dict)
            await websocket_service.broadcast_state(robot_id, state_dict)
            self.last_publish[robot_id] = now
            
        # Optional: Save sample to DB

    def _default_obstacle(self):
        return ObstacleState(detected=False, direction="FRONT", distance_cm=0.0, risk_level="NONE", confidence=0.0)
        
    def _default_orientation(self):
        return OrientationState(heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0, confidence=0.0)
        
    def _default_line(self):
        return LineStateOut(detected=False, position="LOST", normalized_error=0.0, confidence=0.0)
        
    def _default_motion(self):
        return MotionState(state="UNKNOWN", confidence=0.0, possible_stall=False)
        
    def _default_tilt(self):
        return TiltState(unsafe=False, confidence=0.0)
        
    def _default_impact(self):
        return ImpactState(possible=False, confidence=0.0)

fusion_service = FusionService()
