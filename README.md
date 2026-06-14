# 🧩 REX-47 Sensor Fusion

> **Repository `09`** · Advanced algorithms for combining multi-modal sensor data (LiDAR, IMU, Vision) into a coherent, highly-accurate representation of the environment.

[![Platform](https://img.shields.io/badge/Platform-AI%2FData-blue)]()
[![Language](https://img.shields.io/badge/Language-C%2B%2B-00599C?logo=c%2B%2B)]()
[![Framework](https://img.shields.io/badge/Framework-ROS2-22314E?logo=ros)]()
[![Algorithms](https://img.shields.io/badge/Algorithms-Kalman%20Filters-FF4B4B)]()

---

## 📋 Table of Contents

- [Overview](#-what-is-this-repository)
- [Architecture](#-architecture)
- [Features](#-features)
- [Getting Started](#-getting-started)
- [Fusion Algorithms](#-fusion-algorithms)
- [Dependencies](#-dependencies)
- [Related Repositories](#-related-repositories)

---

## 🧭 What Is This Repository?

The **Sensor Fusion** service is responsible for tackling the problem of noisy and contradictory sensor data. By applying probabilistic models to data ingested from the Telemetry Service, it provides the Navigation Engine with an extremely accurate, low-latency estimate of the robot's pose and surroundings.

**Key Highlights:**
- ✅ **Extended Kalman Filters (EKF):** Blends high-frequency IMU data with lower-frequency Odometry and Visual SLAM inputs.
- ✅ **Point Cloud Registration:** Cleans and aligns 2D/3D LiDAR scans to create dense local occupancy grids.
- ✅ **Fault Tolerance:** Automatically detects sensor degradation (e.g., blinded camera) and heavily weights remaining functional sensors.

---

## 🏗️ Architecture

### Directory Structure

```
09-rex-sensor-fusion/
├── include/              ← C++ Header files
├── src/
│   ├── filters/          ← Implementations of EKF and UKF
│   ├── pointcloud/       ← Algorithms for filtering and clustering LiDAR data
│   ├── nodes/            ← ROS2 Node definitions for publish/subscribe
│   └── main.cpp          ← Application entry point
├── launch/               ← ROS2 Launch files
├── config/               ← YAML parameter files tuning filter covariances
├── CMakeLists.txt        ← Build configuration
├── package.xml           ← ROS2 package metadata
└── README.md             ← This documentation
```

---

## 🎨 Features

### 🧮 **State Estimation**

| Feature | Description |
|---------|-------------|
| **6-DOF Pose Tracking** | Calculates absolute X,Y,Z and Roll,Pitch,Yaw in real-time. |
| **Odometry Fusion** | Combines wheel encoders with visual odometry. |

### 🌐 **Environment Mapping**

| Feature | Description |
|---------|-------------|
| **Occupancy Grid** | Generates a 2D map of obstacles for the Navigation Engine. |
| **Outlier Rejection** | Uses RANSAC to remove noise and reflections from LiDAR scans. |

---

## 🚀 Getting Started

### Prerequisites

- **Ubuntu 22.04** (Recommended)
- **ROS2 Humble**
- C++17 Compiler

### Installation

```bash
# 1. Clone into your ROS2 workspace
cd ~/ros2_ws/src
git clone https://github.com/thathsarabandara/09-rex-sensor-fusion.git

# 2. Install dependencies
rosdep install -i --from-path src --rosdistro humble -y

# 3. Build the package
cd ~/ros2_ws
colcon build --packages-select rex_sensor_fusion
```

### Running the Node

```bash
source install/setup.bash
ros2 launch rex_sensor_fusion fusion.launch.py
```

---

## 🔬 Fusion Algorithms

This service primarily relies on a loosely-coupled **Extended Kalman Filter (EKF)**.
- **Prediction Step:** Driven entirely by the 6-axis IMU (Accelerometer + Gyroscope) running at 200Hz.
- **Correction Step:** Updates the state utilizing LiDAR odometry (10Hz) and visual tracking data (30Hz).

---

## 🔗 Related Repositories

- [08-rex-telemetry-service](../08-rex-telemetry-service) — Provides the raw IMU/Encoder data.
- [10-rex-navigation-engine](../10-rex-navigation-engine) — Consumes the fused pose and occupancy grids.
- [11-rex-vision-ai](../11-rex-vision-ai) — Provides the visual odometry inputs.
