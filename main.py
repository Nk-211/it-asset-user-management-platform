from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

app = FastAPI()

DATABASE_URL = "sqlite:///./assets.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# -------------------------
# DATABASE MODELS
# -------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, default="Active")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String, unique=True, nullable=False)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    serial_number = Column(String, nullable=False)
    os = Column(String, nullable=False)
    status = Column(String, default="Available")
    assigned_user = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# -------------------------
# API
# -------------------------

@app.post("/users")
def create_user(
    name: str,
    department: str,
    role: str,
    status: str = "Active"
):
    db = SessionLocal()

    user = User(
        name=name,
        department=department,
        role=role,
        status=status
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id
    db.close()

    return {
        "message": "User created successfully",
        "user_id": user_id
    }


@app.get("/users")
def get_users():
    db = SessionLocal()
    users = db.query(User).all()

    result = [
        {
            "id": user.id,
            "name": user.name,
            "department": user.department,
            "role": user.role,
            "status": user.status
        }
        for user in users
    ]

    db.close()

    return result


@app.post("/devices")
def create_device(
    asset_tag: str,
    manufacturer: str,
    model: str,
    serial_number: str,
    os: str,
    status: str = "Available"
):
    db = SessionLocal()

    existing = db.query(Device).filter(
        Device.asset_tag == asset_tag
    ).first()

    if existing:
        db.close()
        return {
            "error": "Asset tag already exists"
        }

    device = Device(
        asset_tag=asset_tag,
        manufacturer=manufacturer,
        model=model,
        serial_number=serial_number,
        os=os,
        status=status
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    device_id = device.id
    db.close()

    return {
        "message": "Device created successfully",
        "device_id": device_id
    }


@app.get("/devices")
def get_devices():
    db = SessionLocal()
    devices = db.query(Device).all()

    result = [
        {
            "id": device.id,
            "asset_tag": device.asset_tag,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "serial_number": device.serial_number,
            "os": device.os,
            "status": device.status,
            "assigned_user": device.assigned_user
        }
        for device in devices
    ]

    db.close()

    return result


@app.patch("/devices/{device_id}/assign")
def assign_device(device_id: int, user: str):
    db = SessionLocal()

    device = db.query(Device).filter(
        Device.id == device_id
    ).first()

    if not device:
        db.close()
        return {
            "error": "Device not found"
        }

    device.assigned_user = user
    device.status = "Assigned"

    db.commit()
    db.refresh(device)

    db.close()

    return {
        "message": "Device assigned successfully",
        "device_id": device_id,
        "assigned_user": user
    }


# -------------------------
# WEB APPLICATION
# -------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    db = SessionLocal()

    users = db.query(User).all()
    devices = db.query(Device).all()

    db.close()

    user_rows = ""

    for user in users:
        user_rows += f"""
        <tr>
            <td>{user.id}</td>
            <td>{user.name}</td>
            <td>{user.department}</td>
            <td>{user.role}</td>
            <td>{user.status}</td>
        </tr>
        """

    device_rows = ""

    for device in devices:
        device_rows += f"""
        <tr>
            <td>{device.asset_tag}</td>
            <td>{device.manufacturer}</td>
            <td>{device.model}</td>
            <td>{device.os}</td>
            <td>{device.status}</td>
            <td>{device.assigned_user or "Unassigned"}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IT Asset & User Management</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6f8;
                margin: 0;
                padding: 30px;
            }}

            .container {{
                max-width: 1100px;
                margin: auto;
            }}

            h1 {{
                color: #222;
            }}

            .card {{
                background: white;
                padding: 25px;
                margin-bottom: 25px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}

            input, select {{
                width: 100%;
                padding: 10px;
                margin: 7px 0 15px;
                border: 1px solid #ccc;
                border-radius: 5px;
                box-sizing: border-box;
            }}

            button {{
                padding: 11px 20px;
                background: #222;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}

            button:hover {{
                opacity: 0.85;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}

            th, td {{
                padding: 12px;
                border-bottom: 1px solid #ddd;
                text-align: left;
            }}

            th {{
                background: #f0f0f0;
            }}

            .message {{
                margin-top: 15px;
                font-weight: bold;
            }}
        </style>
    </head>

    <body>

    <div class="container">

        <h1>IT Asset & User Management Platform</h1>

        <!-- ADD USER -->

        <div class="card">

            <h2>Add New User</h2>

            <form id="userForm">

                <label>Name</label>
                <input
                    type="text"
                    id="name"
                    placeholder="Enter full name"
                    required
                >

                <label>Department</label>
                <input
                    type="text"
                    id="department"
                    placeholder="Enter department"
                    required
                >

                <label>Role</label>
                <input
                    type="text"
                    id="role"
                    placeholder="Enter job role"
                    required
                >

                <label>Status</label>

                <select id="status">
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                    <option value="On Leave">On Leave</option>
                </select>

                <button type="submit">
                    Add User
                </button>

            </form>

            <div id="userMessage" class="message"></div>

        </div>


        <!-- USERS -->

        <div class="card">

            <h2>Users</h2>

            <table>

                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Role</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tbody id="usersTable">

                    {user_rows}

                </tbody>

            </table>

        </div>


        <!-- DEVICES -->

        <div class="card">

            <h2>IT Assets / Devices</h2>

            <table>

                <thead>
                    <tr>
                        <th>Asset Tag</th>
                        <th>Manufacturer</th>
                        <th>Model</th>
                        <th>OS</th>
                        <th>Status</th>
                        <th>Assigned User</th>
                    </tr>
                </thead>

                <tbody>

                    {device_rows}

                </tbody>

            </table>

        </div>

    </div>


    <script>

        document
            .getElementById("userForm")
            .addEventListener("submit", async function(event) {{

                event.preventDefault();

                const name =
                    document.getElementById("name").value;

                const department =
                    document.getElementById("department").value;

                const role =
                    document.getElementById("role").value;

                const status =
                    document.getElementById("status").value;

                const params = new URLSearchParams({{
                    name: name,
                    department: department,
                    role: role,
                    status: status
                }});

                const response = await fetch(
                    "/users?" + params.toString(),
                    {{
                        method: "POST"
                    }}
                );

                const data = await response.json();

                const message =
                    document.getElementById("userMessage");

                if (response.ok) {{

                    message.textContent =
                        "User added successfully. User ID: "
                        + data.user_id;

                    document
                        .getElementById("userForm")
                        .reset();

                    setTimeout(function() {{
                        location.reload();
                    }}, 800);

                }} else {{

                    message.textContent =
                        "Failed to add user.";

                }}

            }});

    </script>

    </body>
    </html>
    """

    return HTMLResponse(content=html)