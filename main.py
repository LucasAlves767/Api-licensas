from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
import json, os, secrets, string

app = Flask(__name__)

# ================================
# CONFIG
# ================================
ADMIN_TOKEN = "ADMIN_TOKEN_SUPER_SECRETO"
DATA_FILE = "licencas.json"

# ================================
# BANCO SIMPLES (JSON)
# ================================
def load_licencas():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_licencas(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================================
# 🔥 VALIDAÇÃO PRINCIPAL (SEU APP USA)
# ================================
@app.route("/", methods=["POST"])
def validar_licenca():
    data = request.json

    email = data.get("usuario_nome")  # IMPORTANTÍSSIMO

    licencas = load_licencas()
    lic = licencas.get(email)

    if not lic:
        return jsonify({
            "ativo": False,
            "mensagem": "Licença não encontrada"
        }), 403

    if not lic.get("ativo"):
        return jsonify({
            "ativo": False,
            "mensagem": "Acesso bloqueado"
        }), 403

    # valida expiração
    try:
        exp = datetime.strptime(lic["expira_em"], "%Y-%m-%d")
        if datetime.now() > exp:
            return jsonify({
                "ativo": False,
                "mensagem": "Licença expirada"
            }), 403
    except:
        pass

    return jsonify({
        "ativo": True,
        "mensagem": "OK",
        "expira_em": lic["expira_em"]
    })

# ================================
# 🔥 GERAR LICENÇA
# ================================
@app.route('/admin/licencas/gerar', methods=['POST'])
def gerar():
    if request.headers.get("Authorization") != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    
    data = request.json
    nome = data.get("nome")
    email = data.get("email")
    dias = int(data.get("dias", 30))

    # gerar senha
    caracteres = string.ascii_uppercase + string.digits
    senha_gerada = ''.join(secrets.choice(caracteres) for _ in range(8))

    licencas = load_licencas()
    data_expira = datetime.now(timezone.utc) + timedelta(days=dias)

    licencas[email] = {
        "nome": nome,
        "email": email,
        "chave": senha_gerada,
        "ativo": True,
        "expira_em": data_expira.strftime("%Y-%m-%d")
    }

    save_licencas(licencas)

    return jsonify({
        "status": "sucesso",
        "senha": senha_gerada
    })

# ================================
# 🔥 LISTAR LICENÇAS
# ================================
@app.route('/admin/licencas', methods=['GET'])
def listar():
    if request.headers.get("Authorization") != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401

    return jsonify(load_licencas())

# ================================
# 🔥 BLOQUEAR LICENÇA
# ================================
@app.route('/admin/licencas/remover/<email>', methods=['DELETE'])
def remover(email):
    if request.headers.get("Authorization") != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401

    licencas = load_licencas()

    if email in licencas:
        licencas[email]["ativo"] = False
        save_licencas(licencas)

    return jsonify({"ok": True})

# ================================
# START
# ================================
if __name__ == "__main__":
    app.run(debug=True)
