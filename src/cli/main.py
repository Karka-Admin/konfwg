import typer

app = typer.Typer(no_args_is_help=True)

@app.command()
def status():
    print("Well atleast the command is running!")

@app.command()
def show(argument: str):
    """
    Display information for specified argument
    
    :param argument: argument information to be displayed
    :type argument: str
    
    Available arguments
    -----------------
    config
    peers
    """
    if argument == "config":
        config = open("/etc/konfwg/konfwg.conf", 'r').read()
        print("\n" + config)
    elif argument == "peers":
        print("SHOW PEERS NOT IMPLEMENTED CURRENTLY!")

@app.command()
def add(peer: str):
    print(f"Adding peer {peer} not implemented yet!")

@app.command()
def update(peer: str):
    print(f"Updating peer {peer} not implemented yet!")

@app.command()
def delete(peer: str):
    print(f"Deleting peer {peer} not implemented yet!")