from app import create_app

app = create_app()

if __name__ == "__main__":
    #debug: 수정시 실시간 반영
    #port:docker-compose와 일치하도록 조절
    app.run(host="0.0.0.0", port=5000, debug=True)
    