from app import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host=app.config["HTTP_HOST"], port=app.config["HTTP_PORT"], debug=False)
