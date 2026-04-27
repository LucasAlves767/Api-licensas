from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import json, os

app = Flask(__name__)
CORS(app)

DB_FILE = "licencas.json"
ADMIN_TOKEN = "ADMIN_TOKEN_SUPER_SECRETO" 

def load_licencas():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_licencas(dados):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

@app.route('/licenca/verificar', methods=['POST'])
def verificar():
    data = request.json
    uid = data.get("usuario_id")
    licencas = load_licencas()
    if uid not in licencas:
        return jsonify({"ativo": False, "mensagem": "Licença não encontrada."}), 403
    
    lic = licencas[uid]
    hoje = datetime.now(timezone.utc)
    data_exp = datetime.fromisoformat(lic["expira_em"].replace("Z", "+00:00"))

    if hoje > data_exp:
        return jsonify({"ativo": False, "mensagem": "Sua licença expirou!"}), 403
    if not lic.get("ativo", True):
        return jsonify({"ativo": False, "mensagem": "Acesso suspenso."}), 403
    return jsonify({"ativo": True, "mensagem": "OK"})

@app.route('/admin/licencas', methods=['GET'])
def listar():
    if request.headers.get("Authorization") != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    return jsonify(load_licencas())

@app.route('/admin/licencas/gerar', methods=['POST'])
def gerar():
    if request.headers.get("Authorization") != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    data = request.json
    uid = data.get("usuario_id")
    dias = int(data.get("dias", 30))
    licencas = load_licencas()
    data_expira = (datetime.now(timezone.utc) + timedelta(days=dias))
    licencas[uid] = {
        "usuario_id": uid,
        "ativo": True,
        "expira_em": data_expira.isoformat(),
        "atualizado_em": datetime.now(timezone.utc).isoformat()
    }
    save_licencas(licencas)
    return jsonify({"status": "sucesso"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
