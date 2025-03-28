import streamlit as st
import os
import hashlib
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Path to the credentials file
CREDENTIALS_FILE = "credentials.json"

def initialize_auth():
    """Initialize authentication in session state."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None

def hash_password(password):
    """Create a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

def save_credentials(username, password, is_admin=False):
    """Save user credentials to the credentials file."""
    # Create credentials file if it doesn't exist
    if not os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump({}, f)
    
    # Load existing credentials
    with open(CREDENTIALS_FILE, 'r') as f:
        credentials = json.load(f)
    
    # Add or update user
    credentials[username] = {
        'password': hash_password(password),
        'is_admin': is_admin
    }
    
    # Save updated credentials
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(credentials, f, indent=4)
    
    return True

def load_credentials():
    """Load user credentials from the credentials file."""
    if not os.path.exists(CREDENTIALS_FILE):
        # Initialize with default admin account if file doesn't exist - THIS NEEDS TO BE REMOVED
        default_admin = os.getenv("DEFAULT_ADMIN_USER", "omg_he_left_default_stuff")
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "N1ceTryN00b")
        save_credentials(default_admin, default_password, is_admin=True)
        print(f"Created initial admin account: {default_admin} / {default_password}")
        
    with open(CREDENTIALS_FILE, 'r') as f:
        return json.load(f)

def verify_credentials(username, password):
    """Verify user credentials."""
    credentials = load_credentials()
    
    if username in credentials:
        stored_hash = credentials[username]['password']
        input_hash = hash_password(password)
        if stored_hash == input_hash:
            return True, credentials[username].get('is_admin', False)
    
    return False, False

def login_user(username, password):
    """Attempt to log in a user with provided credentials."""
    is_valid, is_admin = verify_credentials(username, password)
    
    if is_valid:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.is_admin = is_admin
        return True
    else:
        return False

def logout_user():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.is_admin = False

def show_login_page():
    """Display the login page."""
    st.title("GreenTracCoder Login")
    
    st.markdown("""
    ### Welcome to GreenTracCoder
    
    Please enter your credentials to access the application.
    """)
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if login_user(username, password):
                st.success("Login successful!")
                st.rerun()  # Rerun to show the main application
            else:
                st.error("Invalid username or password")

def show_logout_button():
    """Display logout button in the sidebar."""
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username}**")
        if st.button("Logout"):
            logout_user()
            st.rerun()  # Rerun to show login page

def require_login(function):
    """Decorator to require login before accessing a function."""
    def wrapper(*args, **kwargs):
        initialize_auth()
        
        if st.session_state.authenticated:
            # User is authenticated, show the logout button and run the function
            show_logout_button()
            return function(*args, **kwargs)
        else:
            # User is not authenticated, show login page
            show_login_page()
            return None
    
    return wrapper

def admin_panel():
    """Admin panel for user management."""
    if not st.session_state.get('is_admin', False):
        st.warning("You must be an admin to access this area.")
        return
    
    st.title("User Management")
    
    # Load current users
    credentials = load_credentials()
    
    st.subheader("Current Users")
    
    # Display users table
    users_data = []
    for username, data in credentials.items():
        users_data.append({
            "Username": username,
            "Admin": "Yes" if data.get('is_admin', False) else "No"
        })
    
    if users_data:
        st.table(users_data)
    else:
        st.info("No users found.")
    
    # Add new user form
    st.subheader("Add New User")
    
    with st.form("add_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        is_admin = st.checkbox("Is Admin")
        
        submit = st.form_submit_button("Add User")
        
        if submit:
            if not new_username: 
                st.error("Username cannot be empty")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif new_username in credentials:
                st.error(f"User '{new_username}' already exists")
            else:
                save_credentials(new_username, new_password, is_admin)
                st.success(f"User '{new_username}' added successfully")
                st.rerun()  # Refresh the page to show the new user
    
    # Change password form
    st.subheader("Change Password")
    
    with st.form("change_password_form"):
        username_to_change = st.selectbox("User", list(credentials.keys()))
        new_password = st.text_input("New Password", type="password", key="change_pw")
        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_change_pw")
        
        submit = st.form_submit_button("Change Password")
        
        if submit:
            if new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                # Keep the same admin status
                is_admin = credentials[username_to_change].get('is_admin', False)
                save_credentials(username_to_change, new_password, is_admin)
                st.success(f"Password for '{username_to_change}' changed successfully")

# We do NOT need a create_initial_admin function since load_credentials handles it
# Just calling load_credentials() once when this module is imported to ensure credentials file exists
load_credentials()
