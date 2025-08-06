import os
import json
import logging
from pathlib import Path

# --- Configuração ---

# O URL ANTIGO que será substituído (se encontrado).
OLD_BASE_URL = "https://pub-aa2c224cdafd4102bd407024bb5282ff.r2.dev/cze-and-peku/"

# O prefixo de caminho LOCAL que também será substituído (se encontrado).
LOCAL_PREFIX = "modules/"

# O URL NOVO que será usado em todas as substituições.
NEW_BASE_URL = "https://assets.yanbraga.com/cze-and-peku/"

# O caminho para a pasta do seu módulo consolidado.
# Verifique se este caminho está correto antes de executar.
CONSOLIDATED_MODULE_DIR = Path(r"C:\Users\Yanbd\foundry-data\v11\Data\Data\modules\yan-curated-czepeku")

# --- Configuração de Logging ---
# Cria um arquivo de log para registrar todas as alterações.
log_file_path = CONSOLIDATED_MODULE_DIR / "asset_update.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='w'),
        logging.StreamHandler()
    ]
)

def update_paths_in_json(json_obj, old_url, new_url, local_prefix):
    """
    Função recursiva para encontrar e substituir caminhos de assets em um objeto JSON.
    Ele lida com dois casos: substituição de uma URL antiga e substituição de um prefixo de caminho local.
    """
    changes_made = 0
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if isinstance(value, str):
                original_value = value
                new_value = None
                
                # Caso 1: Substitui a URL antiga da Cloudflare.
                if old_url in value:
                    new_value = value.replace(old_url, new_url)
                
                # Caso 2: Substitui o prefixo local 'modules/'.
                elif value.strip().startswith(local_prefix):
                    path_part = value.strip().replace(local_prefix, "", 1)
                    new_value = f"{new_url}{path_part}"

                # Se uma alteração foi feita, atualiza o JSON.
                if new_value and new_value != original_value:
                    json_obj[key] = new_value
                    logging.info(f"    Substituído: '{original_value}' -> '{new_value}'")
                    changes_made += 1

            elif isinstance(value, (dict, list)):
                # Chama a função recursivamente para objetos ou listas aninhadas.
                changes_made += update_paths_in_json(value, old_url, new_url, local_prefix)
    
    elif isinstance(json_obj, list):
        for i, item in enumerate(json_obj):
            # Chama a função recursivamente para itens em uma lista.
            changes_made += update_paths_in_json(item, old_url, new_url, local_prefix)
            
    return changes_made

def process_db_file(db_path, old_url, new_url, local_prefix):
    """
    Processa um único arquivo .db, lendo, atualizando e reescrevendo-o.
    """
    logging.info(f"--- Processando arquivo: {db_path.name} ---")
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(f"  ERRO ao ler o arquivo {db_path.name}: {e}")
        return 0, 0 # Retorna 0 para arquivos processados e alterações

    updated_lines = []
    total_changes = 0
    lines_with_changes = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        try:
            json_data = json.loads(line)
            changes_in_line = update_paths_in_json(json_data, old_url, new_url, local_prefix)
            if changes_in_line > 0:
                total_changes += changes_in_line
                lines_with_changes += 1
            updated_lines.append(json.dumps(json_data, ensure_ascii=False))
        except json.JSONDecodeError:
            logging.warning(f"  Aviso: Linha {i+1} em {db_path.name} não é um JSON válido. Mantendo original.")
            updated_lines.append(line)

    if total_changes > 0:
        try:
            # Escreve as alterações de volta no mesmo arquivo
            with open(db_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(updated_lines) + "\n")
            logging.info(f"  Arquivo {db_path.name} atualizado. {total_changes} alterações em {lines_with_changes} linhas.")
            return 1, total_changes
        except Exception as e:
            logging.error(f"  ERRO ao escrever no arquivo {db_path.name}: {e}")
            return 0, 0
    else:
        logging.info(f"  Nenhuma alteração necessária para {db_path.name}.")
        return 1, 0 # Arquivo processado, mas sem alterações

def main():
    """
    Função principal que encontra e processa todos os arquivos .db.
    """
    packs_dir = CONSOLIDATED_MODULE_DIR / "packs"

    logging.info("Iniciando script de atualização de assets...")
    logging.info(f"Procurando por URL antiga: '{OLD_BASE_URL}'")
    logging.info(f"Procurando por prefixo local: '{LOCAL_PREFIX}'")
    logging.info(f"Substituindo por URL nova: '{NEW_BASE_URL}'")
    logging.info("-" * 50)

    if not packs_dir.is_dir():
        logging.error(f"ERRO: A pasta 'packs' não foi encontrada em: {CONSOLIDATED_MODULE_DIR}")
        logging.error("Verifique se o caminho em CONSOLIDATED_MODULE_DIR está correto.")
        return

    db_files = list(packs_dir.glob("*.db"))
    if not db_files:
        logging.warning(f"Nenhum arquivo .db encontrado em {packs_dir}. Nada a fazer.")
        return

    logging.info(f"Encontrados {len(db_files)} arquivos .db para processar.")
    
    grand_total_changes = 0
    files_processed = 0
    files_modified = 0

    for db_file in db_files:
        processed, changes = process_db_file(db_file, OLD_BASE_URL, NEW_BASE_URL, LOCAL_PREFIX)
        files_processed += processed
        if changes > 0:
            files_modified += 1
            grand_total_changes += changes

    logging.info("--- Processo de atualização concluído ---")
    logging.info(f"Total de arquivos .db encontrados e processados: {files_processed}")
    logging.info(f"Total de arquivos modificados: {files_modified}")
    logging.info(f"Total de caminhos de assets atualizados: {grand_total_changes}")
    logging.info(f"Um log detalhado foi salvo em: {log_file_path}")

if __name__ == "__main__":
    main()
