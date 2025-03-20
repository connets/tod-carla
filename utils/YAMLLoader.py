import yaml

def load_yaml(file_path):
    """Load a YAML file and return its content as a dictionary."""
    file = open (file_path, 'r')
    result = yaml.safe_load(file)
    file.close()
    return result


def load_and_merge_yaml_file(file_path):
    """Load and merge YAML files"""

    base_config = {}
    override_config = load_yaml(file_path)

    # Find the last occurrence of '/' (to get the directory part)
    directory = file_path.rsplit('/', 1)[0]

    if 'super' in override_config:

        superfile = override_config['super']
        base_config = load_and_merge_yaml_file(file_path=f"{directory}/{superfile}")
        # Load the superfile and merge its content with his superfile

    if 'super' in override_config:
        # Remove the 'super' key from the override_config dictionary
        override_config.pop('super', None)
    
    if 'super' in base_config:
        # Remove the 'super' key from the override_config dictionary
        base_config.pop('super', None)

    if 'personalizations' in override_config:
        personalizations = override_config['personalizations']
        override_config = base_config
        for personalization in personalizations:
            override_config = merge_dicts(override_config, load_yaml(f"{directory}/{personalization}"))

        override_config.pop('personalizations', None)
        return override_config

    # Merge the base_config and override_config dictionaries
    base_config = merge_dicts(base_config, override_config)
    
    return base_config

def merge_dicts(base, override):
    """Merge two dictionaries. The override dictionary takes precedence."""
    merged = base.copy()  # Create a copy of the base dictionary
    for key, value in override.items():
        if isinstance(value, dict) and key in merged:
            # Recursively merge nested dictionaries
            merged[key] = merge_dicts(merged[key], value)
        elif isinstance(value, list) and key in merged:
            # Merge lists by actor_id or agentId or x_key
            merged[key] = merge_lists(merged[key], value)
        else:
            # Overwrite the value or add the key if it doesn't exist in the base
            merged[key] = value
    return merged

def merge_lists(base_list, override_list):
    """Merge two lists. If the list items are dicts, merge them by actor_id or agentId or x_key."""
    # Merge logic by primary identifiers ('agentId', 'actor_id', 'x_key')
    base_dict_by_id = {item.get('agentId') or item.get('actor_id'): item for item in base_list}
    
    for override_item in override_list:
        # Identify which key exists in the override item
        identifier = override_item.get('agentId') or override_item.get('actor_id') or override_item.get('x_key')
        
        if identifier:
            if identifier in base_dict_by_id:
                # Merge if the identifier exists in base
                base_dict_by_id[identifier] = merge_dicts(base_dict_by_id[identifier], override_item)
            else:
                # Otherwise, just add the item
                base_dict_by_id[identifier] = override_item

    return list(base_dict_by_id.values())


def compare_dicts(dict1, dict2, path=""):
    """Compare two dictionaries and print the differences."""
    added = {}
    removed = {}
    modified = {}

    # Check for keys in dict1 that are not in dict2
    for key in dict1:
        if key not in dict2:
            removed[key] = dict1[key]
        elif dict1[key] != dict2[key]:
            # If the values are not the same, we need to check if they are dictionaries or lists
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                modified[key] = compare_dicts(dict1[key], dict2[key], path + "." + str(key))
            elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                modified[key] = compare_lists(dict1[key], dict2[key], path + "." + str(key))
            else:
                modified[key] = {"file1": dict1[key], "file2": dict2[key]}
    
    # Check for keys in dict2 that are not in dict1
    for key in dict2:
        if key not in dict1:
            added[key] = dict2[key]
    
    # Print the differences
    print_differences("Added", added)
    print_differences("Removed", removed)
    print_differences("Modified", modified)

    return {"added": added, "removed": removed, "modified": modified}

def compare_lists(list1, list2, path=""):
    """Compare two lists and print the differences."""
    added = []
    removed = []
    modified = []

    # Use indices to compare the lists
    max_len = max(len(list1), len(list2))
    for i in range(max_len):
        if i >= len(list1):
            added.append(list2[i])
        elif i >= len(list2):
            removed.append(list1[i])
        else:
            # Compare items in the list
            if list1[i] != list2[i]:
                if isinstance(list1[i], dict) and isinstance(list2[i], dict):
                    modified.append(compare_dicts(list1[i], list2[i], path + f"[{i}]"))
                else:
                    modified.append({"file1": list1[i], "file2": list2[i]})
    
    print_differences("Added", added)
    print_differences("Removed", removed)
    print_differences("Modified", modified)

    return {"added": added, "removed": removed, "modified": modified}

def print_differences(title, data):
    """Helper function to print the differences in a structured way."""
    if data:
        print(f"\n{title}:")
        print(yaml.dump(data, default_flow_style=False))
    else:
        print(f"\nNo {title.lower()} items.")


# Example usage:
file1 = './exampleFiles/file1.yaml'  # Base YAML file
file2 = './exampleFiles/file2.yaml'  # Override YAML file
file3 = './exampleFiles/file3.yaml'  # Override YAML file


g1 = "./exampleFiles/_generated_file1-comb#file1_x1#file1_y1.yaml"
g2 = "./exampleFiles/_generated_file1-comb#file1_x1#file1_y2.yaml"
g3 = "./exampleFiles/_generated_file1-comb#file1_x2#file1_y1.yaml"
g4 = "./exampleFiles/_generated_file1-comb#file1_x2#file1_y2.yaml"

g1_check = "./exampleFiles/_generated_file1-comb#file1_x1#file1_y1.check.yaml"
g2_check = "./exampleFiles/_generated_file1-comb#file1_x1#file1_y2.check.yaml"
g3_check = "./exampleFiles/_generated_file1-comb#file1_x2#file1_y1.check.yaml"
g4_check = "./exampleFiles/_generated_file1-comb#file1_x2#file1_y2.check.yaml"


if __name__ == "__main__":
    
    try:
        merged_config = load_and_merge_yaml_file(file3)
        print("file3", merged_config == load_yaml("./exampleFiles/check_file3.yaml"))
        #compare_dicts(merged_config, load_yaml("check_file3.yaml"))
        
        #print(yaml.dump(merged_config, default_flow_style=False))
        #print("check")
        #print(yaml.dump(load_yaml("check_file3.yaml"), default_flow_style=False))
    except ValueError as e:
         print(f"Validation error: {e}")

    try:
        merged_config = load_and_merge_yaml_file(file2)
        print("file2", merged_config == load_yaml("./exampleFiles/check_file2.yaml"))
        #print(yaml.dump(merged_config, default_flow_style=False))
    except ValueError as e:
        print(f"Validation error: {e}")

    try:
        merged_config = load_and_merge_yaml_file(file1)
        print("file1", merged_config == load_yaml("./exampleFiles/check_file1.yaml"))
        #print(yaml.dump(merged_config, default_flow_style=False))
    except ValueError as e:
        print(f"Validation error: {e}")

    try:
        merged_config = load_and_merge_yaml_file(g1)
        print("g1", merged_config == load_yaml(g1_check))

        merged_config = load_and_merge_yaml_file(g2)
        print("g2", merged_config == load_yaml(g2_check))

        merged_config = load_and_merge_yaml_file(g3)
        print("g3", merged_config == load_yaml(g3_check))

        merged_config = load_and_merge_yaml_file(g4)
        print("g4", merged_config == load_yaml(g4_check))

    except ValueError as e:
        print(f"Validation error: {e}")

    