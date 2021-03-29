# Blockable.py
# This file implements all the necessary functions for blockable. Running it, will
# currently print out all the layouts html return.

# Import modules and set constants
import json
import os

CONFIG_FILE_NAME = 'netlify.json'
FIELDS_FILE_NAME = 'fields.json'
IMPORT_KEY = "import"
DESINATION = "public_html"
CSS_FILE = "stylesheet.css"
JS_FILE = "javascript.js"


def main():
    # Import arg parse
    import argparse
    
    # Set up arguments
    parser = argparse.ArgumentParser(description='Python based static site generator')
    parser.add_argument('-N', '--netlify', action="store_true", help='Only compiles the Netlify components')
    
    # Parse arguments
    args = vars(parser.parse_args())
    if args["netlify"]:
        create_config()
    else:
        compile_site()


def compile_site():
    # Get list of layouts
    layouts_list = os.listdir("layouts")

    # Get data dict
    data_dict = get_data_dict()

    # Make all folders
    prepare_desination()

    # Get collection
    collection_list = os.listdir("data")
    
    # Loop though data
    for collection in collection_list:
        data_file_list = os.listdir("data/" + collection)
        for data_file in data_file_list:
            
            # Get path
            path = collection + "/" + data_file
            
            # Get layout
            if path in data_dict:
                layout = data_dict[path]
            elif collection in data_dict:
                layout = data_dict[collection]
            else:
                break

            # Get data and html then save
            data = parse_json("data/" + path)
            html = layouts(layout, data)
            save(html, data_file[:-5])


    # Move assets
    move_assets()


def site_data(path):
    # Function to be imported and allow access to site data
    return parse_json("data/" + path + ".json")


def get_data_dict():
    """
    This function creates a returns a mapping from the directory of a json data file
    to the directory of the layout it uses
    """

    # Initialize dict
    data_dict = {}

    # Populate dict
    netlify_config = parse_json("netlify.json")
    for collection in netlify_config["collections"]:
        if "files" in collection: # Collection is layout-based
            for page in collection["files"]:

                # Get import info
                import_name = page["import"]
                break_point = import_name.find("/")

                # Ensure import is layout
                if import_name[:break_point] == "layouts":
                    data_dict[collection["name"] + "/" + page["name"] + ".json"] = import_name[break_point+1:]

        else: # Collection is data-based

           # Get import info
           import_name = collection["import"]
           break_point = import_name.find("/")

           # Ensure import is layout
           if import_name[:break_point] == "layouts":
               data_dict[collection["name"]] = import_name[break_point+1:]

    return data_dict

def prepare_desination():
    # Create new destination folder
    os.system("rm -fdr " + DESINATION)
    os.mkdir(DESINATION)

    # Create asset directories
    for asset in ["css", "js"]:
        for template in ["", "layouts", "blocks"]:
            os.mkdir(DESINATION + "/" + asset + "/" + template)

def move_assets():
    # Move everything in assets folder
    asset_list = os.listdir("assets")
    for asset in asset_list:
        os.system("cp -r assets/" + asset + " " + DESINATION)

def save(html, page_name):
    # Save html with given name
    with open(DESINATION + "/" + page_name + '.html', 'w') as page:
        page.write(html);

def layouts(layout, data):
    # Wrapper function for executing a template
    return execute_template("layouts/" + layout, data)

def blocks(block, data):
    # Wrapper function for executing a template
    return execute_template("blocks/" + block, data)

def execute_template(template_path, data):
    """
    This function accepts a template path and a data json then calls the html
    function of the given template, passing it the data parameter and returns
    the templates output
    """

    # Add template path
    import sys
    sys.path.insert(1, template_path)
    
    # Import html function then clean up sys path
    from index import html as template_function
    sys.modules.pop("index")
    sys.path.remove(template_path)
  
    # Get html
    html = template_function(data)
    
    # Move CSS
    if os.path.isfile(template_path + "/" + CSS_FILE):
        os.system('cp ' + template_path + "/" + CSS_FILE + " " + DESINATION + "/css/" + template_path + ".css")
        html = ("<stylesheet rel='/css/" + template_path + ".css'>") + ("\n" + html)

    # Move JS
    if os.path.isfile(template_path + "/" + JS_FILE):
        os.system('cp ' + template_path + "/" + JS_FILE + " " + DESINATION + "/js/" + template_path + ".js")
        html = (html + "\n") + ("<script rel='/js/" + template_path + ".js'>")

    return html

def create_config():
    # Import main Netlify config
    netlify_config = parse_json(CONFIG_FILE_NAME)

    # Parse Netlify config
    parse_config(netlify_config)
  
    # Save final netlify config file
    with open('config.yml', 'w') as netlify_yml_config:
        json.dump(netlify_config, netlify_yml_config, indent=4)


def parse_config(netlify_config):
    # Get list of collections and then reset list
    collections = netlify_config["collections"]
    netlify_config["collections"] = list()

    # Loop though each collection and parse template_files
    for collection in collections:
        if "files" in collection:
            for layout in collection["files"]:
                import_layout(layout, collection["name"], "file")
        else:
            import_layout(collection, collection["name"], "folder")

        # Add collection to config
        netlify_config["collections"].append(collection)


def import_layout(layout, collection_name, layout_type):
    """
    This function imports a layout by importing the fields and
    removing/adding some extra keys to the dictionary
    """
    # Add layout file/folder
    layout[layout_type] = "data/" + collection_name + "/" + layout["name"] + ".json"

    # Import fields
    import_fields(layout)

    # Remove extra field keys
    layout.pop("widget")
    layout.pop("collapsed")


def import_fields(data):
    """
    This function recursively import fields
    """
    # Check if data has imports
    if IMPORT_KEY not in data:
        return

    # Get import info
    file_dir = data.pop(IMPORT_KEY)
    name = data["name"]
    label = data["label"]

    # Check if final key is in data and create if not
    if "fields" not in data:
        data["fields"] = list()
    
    # Load json
    fields = parse_json(file_dir + '/' + FIELDS_FILE_NAME)
   
    # Parse for imports
    for field in fields:
        import_fields(field)
   
    # Turn into field object
    data["widget"] = "object"
    data["collapsed"] = True
    data["fields"] = fields

def parse_json(file_dir):
    """
    This function accepts the directory of a json file and returns
    a parsed version of the json file
    """

    # Open file and return parsed json
    with open(file_dir, 'r') as file:
        return json.load(file)

# Boilerplate
if __name__ == "__main__":
    main()
