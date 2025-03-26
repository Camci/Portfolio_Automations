import sys
import json
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QListWidget,
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox
)
import boto3
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='app.log')
logging.getLogger().addHandler(logging.StreamHandler())

# Configuration constants - replace with your own
API_BASE_URL = 'https://your-api-gateway-url.execute-api.region.amazonaws.com'
USER_POOL_ID = 'your-cognito-user-pool-id'
REGION = 'your-aws-region'
CACHE_FILE = "tasks_cache.json"

class AdminDashboard(QWidget):
    """
    Admin Dashboard for managing tasks and subtasks.
    This application allows administrators to create and assign tasks to users
    stored in Amazon Cognito, and track those tasks over time.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Dashboard - Task Management")
        self.resize(900, 600)
        self.users = []
        self.tasks = []
        self.init_ui()
        self.fetch_users()
        self.fetch_tasks()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # User Selection
        user_layout = QHBoxLayout()
        user_label = QLabel("Select User:")
        self.user_dropdown = QComboBox()
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.user_dropdown)
        layout.addLayout(user_layout)
        
        # Existing Tasks List
        tasks_label = QLabel("Existing Tasks")
        layout.addWidget(tasks_label)
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)
        
        # New Task Form
        new_task_label = QLabel("Create New Task")
        layout.addWidget(new_task_label)
        form_layout = QFormLayout()
        self.task_name_edit = QLineEdit()
        self.task_date_edit = QLineEdit()
        form_layout.addRow("Task Name:", self.task_name_edit)
        form_layout.addRow("Task Date (YYYY-MM-DD):", self.task_date_edit)
        
        # Connect task date changes to update subtasks
        self.task_date_edit.textChanged.connect(self.update_subtask_dates)
        
        # Subtasks
        self.subtask_edits = []
        self.subtask_date_edits = []
        for i in range(3):
            subtask_edit = QLineEdit()
            subtask_date_edit = QLineEdit()
            # Automatically set subtask dates and prevent manual editing
            subtask_date_edit.setReadOnly(True)
            self.subtask_edits.append(subtask_edit)
            self.subtask_date_edits.append(subtask_date_edit)
            form_layout.addRow(f"Subtask {i+1}:", subtask_edit)
            form_layout.addRow(f"Subtask {i+1} Date:", subtask_date_edit)
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_task_btn = QPushButton("Add Task")
        refresh_tasks_btn = QPushButton("Refresh Tasks")
        button_layout.addWidget(add_task_btn)
        button_layout.addWidget(refresh_tasks_btn)
        layout.addLayout(button_layout)
        
        # Connect signals to slots
        add_task_btn.clicked.connect(self.add_task)
        refresh_tasks_btn.clicked.connect(self.fetch_tasks)
        
        # Set the layout
        self.setLayout(layout)

    def update_subtask_dates(self, new_date):
        """Update all subtask date fields to match the main task date."""
        for subtask_date_edit in self.subtask_date_edits:
            subtask_date_edit.setText(new_date)

    def fetch_users(self):
        """Fetch users from Cognito user pool."""
        try:
            # Initialize Cognito client
            client = boto3.client('cognito-idp', region_name=REGION)
            
            # List users in the user pool
            response = client.list_users(UserPoolId=USER_POOL_ID)
            
            # Process each user
            for user in response['Users']:
                # Extract email attribute
                email = next(attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email')
                user_id = user['Username']
                self.users.append(f"{email} - {user_id}")
                
            # Add users to dropdown
            self.user_dropdown.addItems(self.users)
        except Exception as e:
            logging.error(f"Failed to fetch users: {e}")
            QMessageBox.critical(self, "Error", f"Failed to fetch users: {e}")

    def fetch_tasks(self):
        """Fetch tasks from the API and cache them locally."""
        try:
            # Call the API to get tasks
            response = requests.get(f"{API_BASE_URL}/tasks")
            
            # Check response status
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")
                
            # Parse response data
            data = response.json()
            
            # Save to cache file
            with open(CACHE_FILE, 'w') as cache_file:
                json.dump(data, cache_file)
                
            # Update instance variable and UI
            self.tasks = data
            self.task_list.clear()
            for task in data:
                self.task_list.addItem(task['name'])
                
            QMessageBox.information(self, "Success", "Tasks cached successfully!")
        except Exception as e:
            logging.error(f"Failed to fetch tasks: {e}")
            QMessageBox.critical(self, "Error", f"Failed to fetch tasks: {e}")

    def add_task(self):
        """Add a new task for the selected user."""
        # Validate required fields
        if not self.task_name_edit.text() or not self.task_date_edit.text():
            QMessageBox.critical(self, "Error", "Task Name and Date are required!")
            return
            
        # Create subtasks list
        subtasks = []
        for i in range(3):
            if self.subtask_edits[i].text():
                subtasks.append({
                    'name': self.subtask_edits[i].text(),
                    'date': self.subtask_date_edits[i].text(),
                    'checked': False
                })
                
        # Create task data structure
        task_data = {
            'name': self.task_name_edit.text(),
            'date': self.task_date_edit.text(),
            'checked': False,
            'subtasks': subtasks
        }
        
        # Get selected user
        selected_user = self.user_dropdown.currentText()
        if not selected_user:
            QMessageBox.critical(self, "Error", "Please select a user!")
            return
            
        # Extract user ID from selected item
        user_id = selected_user.split(" - ")[1]
        
        # Create API payload
        payload = {
            'userId': user_id,
            'task': task_data
        }
        
        try:
            # Call API to create task
            response = requests.post(
                f"{API_BASE_URL}/tasks",
                json=payload
            )
            
            # Check response
            if response.status_code in (200, 201):
                QMessageBox.information(self, "Success", "Task added successfully!")
                self.fetch_tasks()  # Refresh task list
            else:
                QMessageBox.critical(self, "Error", f"Failed to add task: {response.text}")
        except Exception as e:
            logging.error(f"Failed to add task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add task: {e}")


# Application entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = AdminDashboard()
    dashboard.show()
    sys.exit(app.exec_()) 