# 🏆 HACKATHON 2025 - COMPREHENSIVE COMPETITION MEMORY

*Last Updated: September 27, 2025*

---

## 📋 **COMPETITION OVERVIEW**

### **🎯 Competition Name**: VÒNG CHUNG KẾT HACKATHON 2025
- **Format**: Robot navigation and task completion
- **Platform**: JetBot with LIDAR, Camera, Motors
- **Duration**: 5 minutes per problem
- **Total Problems**: 3 (A, B, C) with increasing difficulty

---

## 🗺️ **WAREHOUSE STRUCTURE (Kho hàng)**

### **Graph Representation**:
- **G = (V, E)** where:
  - **V (Vertices)**: Start, End, Load, None nodes
  - **E (Edges)**: Connections with costs, NESW directions only (no diagonal)
- **Coordinate System**: Fixed directions N, W, S, E (warehouse-relative, not robot-relative)

### **Map Data Source**:
- **API Endpoint**: `/api/maps/get_active_map`
- **Format**: JSON with "nodes" and "edges" arrays
- **Example Structure**:
```json
{
  "nodes": [
    {"id": 1, "x": 0, "y": 1, "type": "normal"},
    {"id": 2, "x": 0, "y": 2, "type": "start"},
    {"id": 3, "x": 1, "y": 0, "type": "normal"},
    {"id": 4, "x": 1, "y": 1, "type": "normal"},
    {"id": 5, "x": 1, "y": 2, "type": "normal"},
    {"id": 6, "x": 1, "y": 3, "type": "normal"},
    {"id": 7, "x": 2, "y": 0, "type": "normal"},
    {"id": 8, "x": 2, "y": 1, "type": "normal"},
    {"id": 9, "x": 2, "y": 2, "type": "normal"},
    {"id": 10, "x": 2, "y": 3, "type": "normal"},
    {"id": 11, "x": 3, "y": 1, "type": "end"},
    {"id": 12, "x": 3, "y": 2, "type": "normal"},
    {"id": 13, "x": 3, "y": 3, "type": "normal"}
  ],
  "edges": [
    {"source": 1, "target": 2, "label": "S"},
    {"source": 2, "target": 1, "label": "N"},
    {"source": 1, "target": 4, "label": "E"},
    {"source": 4, "target": 1, "label": "W"},
    {"source": 2, "target": 5, "label": "E"},
    {"source": 5, "target": 2, "label": "W"},
    {"source": 3, "target": 4, "label": "S"},
    {"source": 4, "target": 3, "label": "N"},
    {"source": 4, "target": 5, "label": "S"},
    {"source": 5, "target": 4, "label": "N"},
    {"source": 5, "target": 6, "label": "S"},
    {"source": 6, "target": 5, "label": "N"},
    {"source": 3, "target": 7, "label": "E"},
    {"source": 7, "target": 3, "label": "W"},
    {"source": 4, "target": 8, "label": "E"},
    {"source": 8, "target": 4, "label": "W"},
    {"source": 5, "target": 9, "label": "E"},
    {"source": 9, "target": 5, "label": "W"},
    {"source": 6, "target": 10, "label": "E"},
    {"source": 10, "target": 6, "label": "W"},
    {"source": 7, "target": 8, "label": "S"},
    {"source": 8, "target": 7, "label": "N"},
    {"source": 8, "target": 9, "label": "S"},
    {"source": 9, "target": 8, "label": "N"},
    {"source": 9, "target": 10, "label": "S"},
    {"source": 10, "target": 9, "label": "N"},
    {"source": 8, "target": 11, "label": "E"},
    {"source": 11, "target": 8, "label": "W"},
    {"source": 9, "target": 12, "label": "E"},
    {"source": 12, "target": 9, "label": "W"},
    {"source": 10, "target": 13, "label": "E"},
    {"source": 13, "target": 10, "label": "W"},
    {"source": 11, "target": 12, "label": "S"},
    {"source": 12, "target": 11, "label": "N"},
    {"source": 12, "target": 13, "label": "S"},
    {"source": 13, "target": 12, "label": "N"}
  ]
}
```

---

## 🏴 **ITEMS ON ARENA (Sa hình)**

### **Standard Items at Each Intersection**:
1. **🏴 2 Flags**: 
   - **Position**: North-East (NE) và West-South (WS)
   - **Purpose**: LIDAR detection markers

2. **📱 QR Code Sign** (Problems A & B):
   - **Position**: North-East (NE) corner (under flag)
   - **Content**: Node name/identifier

3. **📋 Information Sign** (if present):
   - **Position**: East-South (ES) corner
   - **Content**: Variable data to be read and submitted

### **Additional Items (Problem C Only)**:
4. **🚦 Directional Signs**:
   - **Position**: West-North (WN) corner
   - **Types**: 
     - **Prescriptive** (N, E, S, W): Must go this direction
     - **Prohibitive** (NN, NE, NS, NW): Cannot go this direction
     - **Destination** (L): End point marker

---

## 📚 **PROBLEM DETAILS**

### **🥇 Problem A: Basic Navigation (5 Points)**
#### **Objective**: Move from Start → End
#### **Requirements**:
- Start when flag is raised
- Navigate to End node
- Stop at End for minimum 5 seconds
- Time limit: 5 minutes

#### **Scoring Criteria** (Priority Order):
1. **Completion**: Reach End node successfully
2. **Speed**: Faster completion time
3. **Proximity**: If not completed, closer to End is better

### **🥈 Problem B: Multi-task Navigation (10 Points)**
#### **Objective**: Visit Load nodes → Read signs → Go to End
#### **Requirements**:
- Visit all Load nodes sequentially
- Read Information Signs at each Load node
- Submit sign data to server
- Navigate to End node
- Map provided via API

#### **Scoring Criteria** (Priority Order):
1. **Task Completion**: All signs read successfully
2. **Final Completion**: Reach End node
3. **Speed**: Faster total completion time
4. **Partial Credit**: Number of signs read if incomplete

### **🥉 Problem C: Sign-based Navigation (15 Points)**
#### **Objective**: Navigate using traffic signs only
#### **Requirements**:
- **NO MAP PROVIDED** - navigate by signs only
- Robot starts facing East direction
- Follow directional signs at each intersection
- Read Information Signs when present
- Submit sign data to server
- Reach End node (marked with 'L' sign)

#### **Sign Logic**:
- **Prescriptive Signs** (N,E,S,W): MUST go this direction
- **Prohibitive Signs** (NN,NE,NS,NW): CANNOT go this direction
- **Priority**: Prescriptive > Planned path > Prohibitive (veto power)

#### **Scoring Criteria** (Priority Order):
1. **Completion**: Reach End following all signs correctly
2. **Sign Reading**: Number of Information Signs read
3. **Speed**: Time to completion
4. **Proximity**: Distance from End if incomplete

---

## 🔧 **TECHNICAL SPECIFICATIONS**

### **Server Communication**:
- **Base URL**: `https://hackathon2025-dev.fpt.edu.vn/`
- **Map API**: `GET /api/maps/get_active_map`
- **Submission API**: `POST /api/sign-submissions/submit`

### **Submission Format**:
```json
{
  "text": "<detected_content>",
  "node_id": "<current_node_id>", 
  "token": "<team_token>"
}
```

### **Submission Rules**:
- Maximum 5 submissions per node
- Team-specific token required
- Real-time submission during navigation

---

## ⚖️ **COMPETITION RULES & PENALTIES**

### **🚦 Starting Procedure**:
- Robot placed at Start node center
- Always facing East direction initially
- Waits for flag signal to begin movement

### **🚫 Penalty Actions (Return to Start)**:
- Knocking over any arena items (flags, signs)
- Any wheel completely outside track lines
- Wrong direction travel (Problem C only)
- Backtracking/reversing direction (Problem C only)
- Team decision to restart

### **✅ Node Arrival/Departure**:
- **Arrival**: When robot touches black line at intersection
- **Departure**: When robot completely exits red zone
- **End Completion**: Must stop at End node for minimum 5 seconds

---

## 🏆 **SCORING SYSTEM**

### **Problem A Scoring**:
- **Completion**: 50 points
- **Speed Bonus**: up to 10 points
- **Proximity**: up to 20 points (if incomplete)
- **Maximum**: 80 points

### **Problem B Scoring**:
- **Completion**: 40 points  
- **Sign Reading**: up to 40 points
- **Speed Bonus**: up to 15 points
- **Proximity**: up to 5 points (if incomplete)
- **Maximum**: 100 points

### **Problem C Scoring**:
- **Completion**: 55 points
- **Sign Reading**: up to 55 points
- **Speed Bonus**: up to 5 points
- **Proximity**: up to 5 points (if incomplete)
- **Maximum**: 120 points

### **Final Ranking**:
- **Total Score**: Sum of A + B + C
- **Tie-breaker Priority**: C > B > A performance
- **Maximum Possible**: 300 points

---

## 📝 **REPOSITORY REQUIREMENTS**

### **Mandatory Files**:
- **README.md**: Setup instructions and usage guide
- **SOLUTION.md**: Technical approach and algorithm details
- **Source code**: Organized by problem or unified solution

### **Repository Setup**:
- **Name**: Must match team name exactly
- **Visibility**: Private repository
- **Branch**: Submit via `main` branch
- **Owner**: FPTU-Hackathon-2025 organization

### **Submission Process**:
- Code submission = Push to `main` branch
- Must include complete working solution
- Documentation must be comprehensive

---

## ⏰ **COMPETITION TIMELINE**

### **Competition Day Schedule**:
- **Setup Time**: 5 minutes robot preparation
- **Arena Setup**: 5 minutes arena configuration  
- **Competition Time**: 5 minutes per problem
- **Total per Team**: ~15 minutes active time

### **Judging Process**:
- Real-time performance evaluation
- Automatic scoring system
- Judge verification of rule compliance
- Final ranking based on total points + code quality

---

## 🎯 **STRATEGIC INSIGHTS**

### **Problem Difficulty Analysis**:
- **Problem A**: Entry level - focus on reliability
- **Problem B**: Medium difficulty - API integration + multi-tasking
- **Problem C**: High difficulty - computer vision + real-time decision making

### **Technology Stack Implications**:
- **LIDAR**: Essential for intersection detection
- **Camera**: Critical for sign recognition (YOLO recommended)
- **API Integration**: Required for Problems B & C
- **Path Planning**: A* algorithm recommended for Problems A & B

### **Competition Strategy**:
1. **Guarantee Problem A completion** (5 points baseline)
2. **Optimize Problem B** for consistent 10 points
3. **Attempt Problem C** only if A+B are stable
4. **Focus on reliability over speed** in early problems

---

*📌 **Note**: This memory serves as the definitive reference for HACKATHON 2025 competition rules, scoring, and technical requirements for the NeuroShip team.*