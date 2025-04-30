from datetime import timedelta

# Time intervals for reminders (in minutes)
REMINDER_INTERVAL = 5  # 30 seconds in minutes

# Time intervals for statistics
STATS_INTERVALS = {
    '30m': timedelta(minutes=30),
    '1h': timedelta(hours=1),
    '4h': timedelta(hours=4),
    '10h': timedelta(hours=10),
    '1d': timedelta(days=1),
    '7d': timedelta(days=7)
}

# GPT prompts
PROMPTS = {
    'log_enhancement': """
    You are a helpful assistant that enhances daily logs.
    Please make the following log entry more structured and engaging.
    Add appropriate emojis and improve readability.
    Keep the original meaning but make it more professional and pleasant to read.
    No need to add unnecessary information. Only to the point.
    Log entry: {log_entry}
    """,
    
    'stats_summary_short': """
    You are a helpful assistant that creates summaries of daily activities.
    Please create a structured summary of the following activities for the last {time_period}.
    Organize them in a clear, bullet-point format with appropriate emojis.
    Activities: {activities}
    """,
    
    'stats_summary_long': """
    You are a helpful assistant that creates detailed summaries of daily activities.
    Please create a comprehensive summary of the following activities for the last {time_period}.
    Include a brief analysis of productivity patterns and suggestions for improvement.
    Activities: {activities}
    """
} 