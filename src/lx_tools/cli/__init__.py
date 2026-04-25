from cyclopts import App

from lx_tools.cli.json import app as json_app

app = App()
app.command(json_app)

if __name__ == "__main__":
    app()
