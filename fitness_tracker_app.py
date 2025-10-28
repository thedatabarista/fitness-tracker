import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import json
import os

# Set page config
st.set_page_config(page_title="Bodybuilding Tracker", page_icon="💪", layout="wide")

# Data file paths
WEIGHT_FILE = "weight_data.json"
WORKOUT_FILE = "workout_data.json"
PROFILE_FILE = "profile_data.json"

# Initialize data files if they don't exist
def init_data_files():
    if not os.path.exists(WEIGHT_FILE):
        with open(WEIGHT_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(WORKOUT_FILE):
        with open(WORKOUT_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'w') as f:
            json.dump({
                "name": "",
                "age": 36,
                "weight": 83.25,
                "height": 173,
                "goal_weight": 95,
                "experience": "Beginner"
            }, f)

init_data_files()

# Load data functions
def load_weight_data():
    with open(WEIGHT_FILE, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data) if data else pd.DataFrame(columns=['date', 'weight', 'notes'])

def load_workout_data():
    with open(WORKOUT_FILE, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data) if data else pd.DataFrame(columns=['date', 'exercise', 'sets', 'reps', 'weight', 'rpe', 'notes'])

def load_profile():
    with open(PROFILE_FILE, 'r') as f:
        return json.load(f)

def save_weight_data(df):
    with open(WEIGHT_FILE, 'w') as f:
        json.dump(df.to_dict('records'), f)

def save_workout_data(df):
    with open(WORKOUT_FILE, 'w') as f:
        json.dump(df.to_dict('records'), f)

def save_profile(profile):
    with open(PROFILE_FILE, 'w') as f:
        json.dump(profile, f)

# Sidebar navigation
st.sidebar.title("💪 Navigation")
page = st.sidebar.radio("Go to:", [
    "📊 Dashboard",
    "⚖️ Log Weight", 
    "🏋️ Log Workout",
    "📅 Workout Schedule",
    "📈 Progress Charts",
    "👤 Profile",
    "💾 Export Data"
])

# Load data
weight_df = load_weight_data()
workout_df = load_workout_data()
profile = load_profile()

# ===== DASHBOARD PAGE =====
if page == "📊 Dashboard":
    st.title("💪 Bodybuilding Tracker Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not weight_df.empty:
            current_weight = weight_df.iloc[-1]['weight']
            st.metric("Current Weight", f"{current_weight} kg")
        else:
            st.metric("Current Weight", "No data")
    
    with col2:
        goal_weight = profile.get('goal_weight', 95)
        st.metric("Goal Weight", f"{goal_weight} kg")
    
    with col3:
        if not weight_df.empty:
            weight_to_go = goal_weight - current_weight
            st.metric("Weight to Gain", f"{weight_to_go:.1f} kg")
        else:
            st.metric("Weight to Gain", "No data")
    
    with col4:
        if not workout_df.empty:
            workouts_this_week = len(workout_df[pd.to_datetime(workout_df['date']) >= pd.Timestamp.now() - pd.Timedelta(days=7)])
            st.metric("Workouts This Week", workouts_this_week)
        else:
            st.metric("Workouts This Week", 0)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Recent Weight Trend")
        if not weight_df.empty and len(weight_df) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(weight_df['date']),
                y=weight_df['weight'],
                mode='lines+markers',
                name='Weight',
                line=dict(color='#4CAF50', width=3)
            ))
            fig.add_hline(y=goal_weight, line_dash="dash", line_color="red", annotation_text="Goal")
            fig.update_layout(height=300, xaxis_title="Date", yaxis_title="Weight (kg)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Log at least 2 weight entries to see trend")
    
    with col2:
        st.subheader("🏋️ Recent Workouts")
        if not workout_df.empty:
            recent = workout_df.tail(5)[['date', 'exercise', 'weight', 'rpe']].sort_values('date', ascending=False)
            st.dataframe(recent, hide_index=True, use_container_width=True)
        else:
            st.info("No workouts logged yet")

# ===== LOG WEIGHT PAGE =====
elif page == "⚖️ Log Weight":
    st.title("⚖️ Log Your Weight")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Add New Weight Entry")
        
        with st.form("weight_form"):
            weight_date = st.date_input("Date", value=date.today())
            weight_value = st.number_input("Weight (kg)", min_value=40.0, max_value=200.0, value=83.25, step=0.1)
            notes = st.text_input("Notes (optional)", placeholder="Felt good, measured morning...")
            
            submitted = st.form_submit_button("💾 Save Weight", use_container_width=True)
            
            if submitted:
                new_entry = pd.DataFrame([{
                    'date': weight_date.strftime('%Y-%m-%d'),
                    'weight': weight_value,
                    'notes': notes
                }])
                weight_df = pd.concat([weight_df, new_entry], ignore_index=True)
                weight_df = weight_df.sort_values('date')
                save_weight_data(weight_df)
                st.success("✅ Weight logged successfully!")
                st.rerun()
    
    with col2:
        st.subheader("Quick Stats")
        if not weight_df.empty:
            latest = weight_df.iloc[-1]
            st.metric("Latest Weight", f"{latest['weight']} kg")
            st.metric("Date", latest['date'])
            
            if len(weight_df) > 1:
                prev_weight = weight_df.iloc[-2]['weight']
                change = latest['weight'] - prev_weight
                st.metric("Change from Last", f"{change:+.1f} kg")
        else:
            st.info("No weight data yet")
    
    st.markdown("---")
    
    st.subheader("📋 Weight History")
    if not weight_df.empty:
        display_df = weight_df.copy()
        display_df = display_df.sort_values('date', ascending=False)
        
        # Add delete buttons
        for idx, row in display_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 4, 1])
            col1.write(row['date'])
            col2.write(f"{row['weight']} kg")
            col3.write(row['notes'] if row['notes'] else "-")
            if col4.button("🗑️", key=f"del_weight_{idx}"):
                weight_df = weight_df.drop(idx)
                save_weight_data(weight_df)
                st.rerun()
    else:
        st.info("No weight entries yet. Add your first one above!")

# ===== LOG WORKOUT PAGE =====
elif page == "🏋️ Log Workout":
    st.title("🏋️ Log Your Workout")
    
    # Exercise library
    exercises = [
        "Barbell Squat", "Deadlift", "Bench Press", "Overhead Press", "Barbell Row",
        "Incline Dumbbell Press", "Dumbbell Row", "Lat Pulldown", "Pull-ups",
        "Barbell Curl", "Tricep Pushdown", "Romanian Deadlift", "Leg Press",
        "Bulgarian Split Squat", "Face Pulls", "Dips", "Leg Curl", "Calf Raise",
        "Hammer Curl", "Overhead Tricep Extension"
    ]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Add New Exercise")
        
        with st.form("workout_form"):
            workout_date = st.date_input("Date", value=date.today())
            exercise = st.selectbox("Exercise", exercises)
            
            col_a, col_b = st.columns(2)
            with col_a:
                sets = st.number_input("Sets", min_value=1, max_value=10, value=3)
                reps = st.number_input("Reps", min_value=1, max_value=50, value=8)
            with col_b:
                weight = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=20.0, step=2.5)
                rpe = st.slider("RPE (1-10)", min_value=1, max_value=10, value=8)
            
            notes = st.text_input("Notes (optional)", placeholder="Felt strong, good form...")
            
            submitted = st.form_submit_button("💾 Save Exercise", use_container_width=True)
            
            if submitted:
                # Calculate E1RM and suggested next weight
                e1rm = weight * (1 + reps / 30)
                if rpe <= 8:
                    next_weight = weight * 1.025
                elif rpe == 9:
                    next_weight = weight
                else:
                    next_weight = weight * 0.95
                
                new_entry = pd.DataFrame([{
                    'date': workout_date.strftime('%Y-%m-%d'),
                    'exercise': exercise,
                    'sets': sets,
                    'reps': reps,
                    'weight': weight,
                    'rpe': rpe,
                    'e1rm': round(e1rm, 1),
                    'next_weight': round(next_weight, 1),
                    'volume': sets * reps * weight,
                    'notes': notes
                }])
                workout_df = pd.concat([workout_df, new_entry], ignore_index=True)
                workout_df = workout_df.sort_values('date')
                save_workout_data(workout_df)
                st.success(f"✅ Exercise logged! Next session: {next_weight:.1f} kg")
                st.rerun()
    
    with col2:
        st.subheader("💡 RPE Guide")
        st.write("**7-8:** Moderate effort, 2-3 reps left")
        st.write("**9:** Hard, 1 rep left")
        st.write("**10:** Max effort, 0 reps left")
        
        st.markdown("---")
        
        st.subheader("Today's Progress")
        today = date.today().strftime('%Y-%m-%d')
        today_workouts = workout_df[workout_df['date'] == today]
        if not today_workouts.empty:
            st.metric("Exercises Today", len(today_workouts))
            total_volume = today_workouts['volume'].sum()
            st.metric("Total Volume", f"{total_volume:,.0f} kg")
        else:
            st.info("No exercises logged today")
    
    st.markdown("---")
    
    st.subheader("📋 Recent Workouts")
    if not workout_df.empty:
        recent = workout_df.tail(10).sort_values('date', ascending=False)
        display_cols = ['date', 'exercise', 'sets', 'reps', 'weight', 'rpe', 'next_weight']
        st.dataframe(recent[display_cols], hide_index=True, use_container_width=True)
    else:
        st.info("No workouts logged yet. Add your first one above!")

# ===== WORKOUT SCHEDULE PAGE =====
elif page == "📅 Workout Schedule":
    st.title("📅 Your Workout Schedule")
    
    st.info("💡 This is a suggested 4-day Upper/Lower split. Customize as needed!")
    
    schedule = {
        "Monday": {
            "focus": "Upper Body (Push)",
            "exercises": ["Bench Press", "Overhead Press", "Incline Dumbbell Press", "Tricep Pushdown", "Face Pulls"]
        },
        "Tuesday": {
            "focus": "Lower Body",
            "exercises": ["Barbell Squat", "Romanian Deadlift", "Leg Press", "Leg Curl", "Calf Raise"]
        },
        "Wednesday": {
            "focus": "Rest / Light Cardio",
            "exercises": []
        },
        "Thursday": {
            "focus": "Upper Body (Pull)",
            "exercises": ["Barbell Row", "Pull-ups", "Lat Pulldown", "Barbell Curl", "Hammer Curl"]
        },
        "Friday": {
            "focus": "Lower Body",
            "exercises": ["Deadlift", "Bulgarian Split Squat", "Leg Press", "Leg Curl", "Calf Raise"]
        },
        "Saturday": {
            "focus": "Rest / Active Recovery",
            "exercises": []
        },
        "Sunday": {
            "focus": "Rest",
            "exercises": []
        }
    }
    
    for day, info in schedule.items():
        with st.expander(f"**{day}** - {info['focus']}", expanded=True):
            if info['exercises']:
                st.write("**Exercises:**")
                for exercise in info['exercises']:
                    st.write(f"• {exercise}")
                st.write("")
                st.write("**Suggested:** 3-4 sets of 8-12 reps per exercise")
            else:
                st.write("Rest day - focus on recovery, light stretching, or walking")

# ===== PROGRESS CHARTS PAGE =====
elif page == "📈 Progress Charts":
    st.title("📈 Your Progress")
    
    tab1, tab2, tab3 = st.tabs(["💪 Weight Progress", "🏋️ Lifting Progress", "📊 Volume Analysis"])
    
    with tab1:
        st.subheader("Weight Over Time")
        if not weight_df.empty and len(weight_df) > 1:
            fig = go.Figure()
            
            weight_df_sorted = weight_df.sort_values('date')
            
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(weight_df_sorted['date']),
                y=weight_df_sorted['weight'],
                mode='lines+markers',
                name='Weight',
                line=dict(color='#2196F3', width=3),
                marker=dict(size=8)
            ))
            
            goal_weight = profile.get('goal_weight', 95)
            fig.add_hline(y=goal_weight, line_dash="dash", line_color="red", 
                         annotation_text=f"Goal: {goal_weight} kg")
            
            fig.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title="Weight (kg)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Stats
            col1, col2, col3 = st.columns(3)
            total_change = weight_df_sorted.iloc[-1]['weight'] - weight_df_sorted.iloc[0]['weight']
            col1.metric("Total Change", f"{total_change:+.1f} kg")
            col2.metric("Starting Weight", f"{weight_df_sorted.iloc[0]['weight']} kg")
            col3.metric("Current Weight", f"{weight_df_sorted.iloc[-1]['weight']} kg")
        else:
            st.info("Log at least 2 weight entries to see progress")
    
    with tab2:
        st.subheader("Lifting Progress by Exercise")
        if not workout_df.empty:
            exercise_select = st.selectbox("Select Exercise", workout_df['exercise'].unique())
            
            exercise_data = workout_df[workout_df['exercise'] == exercise_select].sort_values('date')
            
            if len(exercise_data) > 1:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(exercise_data['date']),
                    y=exercise_data['weight'],
                    mode='lines+markers',
                    name='Weight',
                    line=dict(color='#FF5722', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    height=400,
                    xaxis_title="Date",
                    yaxis_title="Weight (kg)",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Progress stats
                col1, col2, col3 = st.columns(3)
                weight_increase = exercise_data.iloc[-1]['weight'] - exercise_data.iloc[0]['weight']
                pct_increase = (weight_increase / exercise_data.iloc[0]['weight']) * 100
                col1.metric("Weight Increase", f"{weight_increase:+.1f} kg")
                col2.metric("% Increase", f"{pct_increase:+.1f}%")
                col3.metric("Sessions", len(exercise_data))
            else:
                st.info(f"Log at least 2 sessions of {exercise_select} to see progress")
        else:
            st.info("No workout data yet")
    
    with tab3:
        st.subheader("Training Volume Over Time")
        if not workout_df.empty:
            # Calculate weekly volume
            workout_df_copy = workout_df.copy()
            workout_df_copy['date'] = pd.to_datetime(workout_df_copy['date'])
            workout_df_copy['week'] = workout_df_copy['date'].dt.to_period('W').astype(str)
            
            weekly_volume = workout_df_copy.groupby('week')['volume'].sum().reset_index()
            
            fig = px.bar(weekly_volume, x='week', y='volume', 
                        labels={'week': 'Week', 'volume': 'Total Volume (kg)'},
                        color_discrete_sequence=['#4CAF50'])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Average Weekly Volume", f"{weekly_volume['volume'].mean():,.0f} kg")
        else:
            st.info("No workout data yet")

# ===== PROFILE PAGE =====
elif page == "👤 Profile":
    st.title("👤 Your Profile")
    
    with st.form("profile_form"):
        name = st.text_input("Name", value=profile.get('name', ''))
        age = st.number_input("Age", min_value=15, max_value=100, value=profile.get('age', 36))
        
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("Starting Weight (kg)", min_value=40.0, max_value=200.0, 
                                    value=float(profile.get('weight', 83.25)), step=0.1)
            height = st.number_input("Height (cm)", min_value=100, max_value=250, 
                                    value=profile.get('height', 173))
        with col2:
            goal_weight = st.number_input("Goal Weight (kg)", min_value=40.0, max_value=200.0, 
                                         value=float(profile.get('goal_weight', 95.0)), step=0.1)
            experience = st.selectbox("Experience Level", 
                                     ["Beginner", "Intermediate", "Advanced"],
                                     index=["Beginner", "Intermediate", "Advanced"].index(profile.get('experience', 'Beginner')))
        
        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)
        
        if submitted:
            profile = {
                'name': name,
                'age': age,
                'weight': weight,
                'height': height,
                'goal_weight': goal_weight,
                'experience': experience
            }
            save_profile(profile)
            st.success("✅ Profile updated successfully!")
            st.rerun()

# ===== EXPORT DATA PAGE =====
elif page == "💾 Export Data":
    st.title("💾 Export Your Data")
    
    st.info("Export your data to Excel or ODS format for backup or external analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export to Excel")
        if st.button("📥 Download Excel File (.xlsx)", use_container_width=True):
            # Create Excel file
            with pd.ExcelWriter('bodybuilding_data.xlsx', engine='openpyxl') as writer:
                if not weight_df.empty:
                    weight_df.to_excel(writer, sheet_name='Weight Log', index=False)
                if not workout_df.empty:
                    workout_df.to_excel(writer, sheet_name='Workout Log', index=False)
                
                # Profile sheet
                profile_df = pd.DataFrame([profile])
                profile_df.to_excel(writer, sheet_name='Profile', index=False)
            
            with open('bodybuilding_data.xlsx', 'rb') as f:
                st.download_button(
                    label="⬇️ Click to Download",
                    data=f,
                    file_name=f'bodybuilding_data_{datetime.now().strftime("%Y%m%d")}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True
                )
    
    with col2:
        st.subheader("Export to CSV")
        if st.button("📥 Download CSV Files (.zip)", use_container_width=True):
            import zipfile
            
            with zipfile.ZipFile('bodybuilding_data.zip', 'w') as zipf:
                if not weight_df.empty:
                    weight_df.to_csv('weight_log.csv', index=False)
                    zipf.write('weight_log.csv')
                if not workout_df.empty:
                    workout_df.to_csv('workout_log.csv', index=False)
                    zipf.write('workout_log.csv')
            
            with open('bodybuilding_data.zip', 'rb') as f:
                st.download_button(
                    label="⬇️ Click to Download",
                    data=f,
                    file_name=f'bodybuilding_data_{datetime.now().strftime("%Y%m%d")}.zip',
                    mime='application/zip',
                    use_container_width=True
                )
    
    st.markdown("---")
    
    st.subheader("📊 Current Data Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Weight Entries", len(weight_df))
    col2.metric("Workout Entries", len(workout_df))
    col3.metric("Unique Exercises", len(workout_df['exercise'].unique()) if not workout_df.empty else 0)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**💪 Bodybuilding Tracker v1.0**")
st.sidebar.markdown("Track your progress, build muscle!")
