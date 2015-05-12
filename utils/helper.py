def extract_params(input_dict, keys_list):
    output_dict = {}
    for key in keys_list:
        output_dict[key] = input_dict.get(key, None)
    return output_dict
