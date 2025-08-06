import os
import json
import shutil
import logging
from pathlib import Path

# --- Configuração ---
# Altere estes caminhos para corresponder à sua estrutura de pastas.
# O script assume que esta é a estrutura de pastas:
# /algum/lugar/
# ├── modules/ (contém todas as pastas de módulos individuais, ex: czepeku-03-land-of-giants)
# └── yan-curated-czepeku/ (seu novo módulo consolidado)
#     ├── module.json
#     └── packs/ (pasta de destino para os arquivos .db)

# Caminho para a pasta que contém TODOS os seus módulos individuais.
SOURCE_MODULES_DIR = Path(r"C:\Users\Yanbd\foundry-data\v11\Data\Data\modules")

# Caminho para a pasta do seu NOVO módulo consolidado.
CONSOLIDATED_MODULE_DIR = Path(r"C:\Users\Yanbd\foundry-data\v11\Data\Data\modules\yan-data-czepeku")

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_db_file_in_module(module_path: Path) -> Path | None:
    """
    Procura por um arquivo .db dentro da pasta de um módulo, priorizando a subpasta 'packs'.
    Retorna o caminho para o primeiro arquivo .db encontrado, ou None se nenhum for encontrado.
    """
    packs_dir = module_path / "packs"
    if not packs_dir.is_dir():
        # Alguns módulos podem ter 'Packs' com 'P' maiúsculo.
        packs_dir = module_path / "Packs"
        if not packs_dir.is_dir():
            logging.warning(f"Pasta 'packs' não encontrada em: {module_path}")
            return None

    # Procura por qualquer arquivo .db dentro da pasta 'packs'.
    db_files = list(packs_dir.glob("*.db"))
    if db_files:
        if len(db_files) > 1:
            logging.warning(f"Múltiplos arquivos .db encontrados em {packs_dir}. Usando o primeiro: {db_files[0]}")
        return db_files[0]
    else:
        logging.warning(f"Nenhum arquivo .db encontrado em: {packs_dir}")
        return None

def main():
    """
    Função principal para executar o script de migração.
    """
    consolidated_json_path = CONSOLIDATED_MODULE_DIR / "module.json"
    destination_packs_dir = CONSOLIDATED_MODULE_DIR / "packs"

    # 1. Validação dos caminhos
    if not SOURCE_MODULES_DIR.is_dir():
        logging.error(f"ERRO: O diretório de módulos de origem não foi encontrado: {SOURCE_MODULES_DIR}")
        return

    if not consolidated_json_path.is_file():
        logging.error(f"ERRO: O arquivo module.json do módulo consolidado não foi encontrado: {consolidated_json_path}")
        return

    # Cria a pasta 'packs' de destino se ela não existir.
    destination_packs_dir.mkdir(exist_ok=True)
    logging.info(f"Diretório de destino dos packs: {destination_packs_dir}")

    # 2. Carregar o module.json consolidado
    try:
        with open(consolidated_json_path, 'r', encoding='utf-8') as f:
            module_data = json.load(f)
        logging.info(f"Arquivo '{consolidated_json_path.name}' carregado com sucesso.")
    except json.JSONDecodeError as e:
        logging.error(f"ERRO: Falha ao decodificar o JSON em {consolidated_json_path}. Verifique a sintaxe. Erro: {e}")
        return
    except Exception as e:
        logging.error(f"ERRO: Não foi possível ler o arquivo {consolidated_json_path}. Erro: {e}")
        return

    packs_to_process = module_data.get("packs", [])
    if not packs_to_process:
        logging.warning("Nenhum 'pack' encontrado no module.json. Nada a fazer.")
        return

    logging.info(f"Encontrados {len(packs_to_process)} packs para processar.")
    
    # 3. Iterar sobre cada pack e realizar a cópia/renomeação
    success_count = 0
    fail_count = 0

    for pack_info in packs_to_process:
        pack_name = pack_info.get("name")
        pack_path_str = pack_info.get("path")

        if not pack_name or not pack_path_str:
            logging.warning(f"Entrada de pack inválida no JSON, pulando: {pack_info}")
            fail_count += 1
            continue

        logging.info(f"--- Processando pack: '{pack_name}' ---")
        
        # O nome da pasta de origem geralmente corresponde ao 'name' do pack.
        # Vamos procurar por uma pasta que COMECE com esse nome para ser mais flexível.
        source_module_folder_name = pack_name
        
        # Tentamos encontrar a pasta do módulo de origem.
        # Isso lida com casos como 'czepeku-12-Adventurers-Guildhall' vs 'czepeku-12-adventurers-guildhall'
        possible_folders = [d for d in SOURCE_MODULES_DIR.iterdir() if d.is_dir() and d.name.lower().startswith(source_module_folder_name.lower())]

        if not possible_folders:
            logging.error(f"FALHA: Não foi possível encontrar a pasta do módulo de origem para '{pack_name}' em {SOURCE_MODULES_DIR}")
            fail_count += 1
            continue
        
        source_module_path = possible_folders[0]
        if len(possible_folders) > 1:
            logging.warning(f"Múltiplas pastas correspondentes encontradas para '{pack_name}'. Usando a primeira: {source_module_path.name}")
            
        logging.info(f"Pasta de origem encontrada: '{source_module_path.name}'")

        # Encontrar o arquivo .db dentro da pasta do módulo de origem.
        source_db_file = find_db_file_in_module(source_module_path)

        if not source_db_file:
            logging.error(f"FALHA: Não foi possível encontrar o arquivo .db para o pack '{pack_name}' dentro de '{source_module_path}'")
            fail_count += 1
            continue
            
        logging.info(f"Arquivo .db de origem encontrado: '{source_db_file.name}'")

        # Definir o caminho de destino a partir do 'path' no module.json
        destination_file_path = destination_packs_dir / Path(pack_path_str).name

        # 4. Copiar e renomear o arquivo
        try:
            shutil.copy2(source_db_file, destination_file_path)
            logging.info(f"SUCESSO: Copiado '{source_db_file.name}' para '{destination_file_path.name}'")
            success_count += 1
        except Exception as e:
            logging.error(f"FALHA: Não foi possível copiar '{source_db_file}' para '{destination_file_path}'. Erro: {e}")
            fail_count += 1

    logging.info("--- Processo de migração concluído ---")
    logging.info(f"Total de packs processados com sucesso: {success_count}")
    logging.info(f"Total de falhas: {fail_count}")

if __name__ == "__main__":
    main()
