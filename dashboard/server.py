import uvicorn

def main():
    print("Starting IICPC Operator Dashboard Backend Server...")
    uvicorn.run("dashboard.app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
