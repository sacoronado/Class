import modal

image = modal.Image.debian_slim().pip_install(
    "streamlit",
    "pandas", 
    "plotly",
    "supabase",
    "python-dotenv"
)

app = modal.App("cage-matcher", image=image)

@app.function(
    secrets=[modal.Secret.from_name("my-supabase-secret")],
    timeout=600,
)
@modal.web_server(8000)
def run():
    import subprocess
    import sys
    
    # Use Python module approach instead of direct command
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "/root/app.py",
        "--server.port=8000",
        "--server.enableCORS=false", 
        "--server.enableXsrfProtection=false",
        "--server.headless=true",
        "--browser.serverAddress=0.0.0.0"
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    app.serve()