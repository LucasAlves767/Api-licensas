from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import json, os, secrets, string

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ================================
# CONFIG
# ================================
ADMIN_TOKEN = "ADMIN_TOKEN_SUPER_SECRETO"
DATA_FILE = "licencas.json"

# ================================
# BANCO (JSON)
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
# VALIDAÇÃO  POST /
# Recebe: usuario_nome (email) + senha (chave)
# ================================
@app.route("/", methods=["POST"])
def validar_licenca():
    try:
        data  = request.json
        email = data.get("usuario_nome")
        chave = data.get("senha")

        if not email or not chave:
            return jsonify({"ativo": False, "mensagem": "Dados incompletos"}), 400

        licencas = load_licencas()
        lic = licencas.get(email)

        if not lic:
            return jsonify({"ativo": False, "mensagem": "Licença não encontrada"}), 403

        if not lic.get("ativo"):
            return jsonify({"ativo": False, "mensagem": "Acesso bloqueado"}), 403

        # ✅ Verifica a chave
        if chave != lic.get("chave"):
            return jsonify({"ativo": False, "mensagem": "Chave inválida"}), 403

        # ✅ Verifica expiração
        try:
            exp = datetime.strptime(lic["expira_em"], "%Y-%m-%d")
            if datetime.now() > exp:
                return jsonify({"ativo": False, "mensagem": "Licença expirada"}), 403
        except Exception:
            return jsonify({"ativo": False, "mensagem": "Erro na data da licença"}), 500

        return jsonify({
            "ativo":     True,
            "mensagem":  "OK",
            "expira_em": lic["expira_em"]
        })

    except Exception as e:
        return jsonify({"ativo": False, "mensagem": str(e)}), 500

# ================================
# GERAR LICENÇA
# ================================
@app.route('/admin/licencas/gerar', methods=['POST'])
def gerar():
    if request.headers.get("Authorization", "").strip() != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401

    data  = request.json
    nome  = data.get("nome")
    email = data.get("email")
    dias  = int(data.get("dias", 30))

    if not email:
        return jsonify({"erro": "Email obrigatório"}), 400

    chave  = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    expira = datetime.now(timezone.utc) + timedelta(days=dias)

    licencas = load_licencas()
    licencas[email] = {
        "nome":      nome,
        "email":     email,
        "chave":     chave,
        "ativo":     True,
        "expira_em": expira.strftime("%Y-%m-%d")
    }
    save_licencas(licencas)

    return jsonify({"status": "sucesso", "senha": chave})

# ================================
# LISTAR
# ================================
@app.route('/admin/licencas', methods=['GET'])
def listar():
    if request.headers.get("Authorization", "").strip() != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    return jsonify(load_licencas())

# ================================
# BLOQUEAR
# ================================
@app.route('/admin/licencas/remover/<email>', methods=['DELETE'])
def remover(email):
    if request.headers.get("Authorization", "").strip() != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    licencas = load_licencas()
    if email in licencas:
        licencas[email]["ativo"] = False
        save_licencas(licencas)
    return jsonify({"ok": True})

# ================================
# EXCLUIR
# ================================
@app.route('/admin/licencas/excluir/<email>', methods=['DELETE'])
def excluir(email):
    if request.headers.get("Authorization", "").strip() != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    licencas = load_licencas()
    if email in licencas:
        del licencas[email]
        save_licencas(licencas)
    return jsonify({"ok": True})

# ================================
# START
# ================================
if __name__ == "__main__":
    app.run(debug=True)
