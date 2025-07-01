import json
import os
import datetime

def print_json_for_llm_help(file_paths: list, output_folder: str) -> None:
    # print_files -> execução gera um arquivo JSON com o conteúdo dos arquivos da variável file_paths.
    #   o arquivo será gerado na pasta output_folder. 
    #   o JSON serve para ser compartilhado com LLMs como chatgpt e claude!!!

    # Create the output file name with the date and counter
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    date_str = datetime.datetime.now().strftime("%Y_%m_%d")
    counter = 1
    while True:
        output_file = os.path.join(
            output_folder, f"{date_str}_{counter:02d}_project_export.json"
        )
        if not os.path.exists(output_file):
            break
        counter += 1

    code_data = {}
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                #code_data[os.path.basename(file_path)] = f.read()
                code_data[file_path] = f.read()
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"An error occurred while processing {file_path}: {e}")

    # Save the data to the JSON file
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(code_data, json_file, indent=4, ensure_ascii=False)
        
    print(f"\n{output_file} saved\n")
