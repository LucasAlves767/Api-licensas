from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import json, os

app = Flask(__name__)
CORS(app)

DB_FILE = "licencas.json"
# Altere este token para o que você quiser usar no seu painel admin.html
ADMIN_TOKEN = "ADMIN_TOKEN_SUPER_SECRETO" 

def load_licencas():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_licencas(dados):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

# ROTA DE VERIFICAÇÃO (USADA PELO APP.PY)
@app.route('/licenca/verificar', methods=['POST'])
def verificar():
    data = request.json
    uid = data.get("usuario_id")
    licencas = load_licencas()
    
    if uid not in licencas:
        return jsonify({"ativo": False, "mensagem": "Licença não encontrada."}), 403
    
    lic = licencas[uid]
    hoje = datetime.now(timezone.utc)
    
    # Converte a data do JSON para comparação
    try:
        data_exp = datetime.fromisoformat(lic["expira_em"].replace("Z", "+00:00"))
    except:
        return jsonify({"ativo": False, "mensagem": "Erro no formato da data."}), 500

    # Bloqueio Automático por Data (90 dias ou qualquer valor)
    if hoje > data_exp:
        return jsonify({"ativo": False, "mensagem": f"Acesso expirado em {data_exp.strftime('%d/%m/%Y')}."}), 403
    
    # Bloqueio Manual (Botão no painel)
    if not lic.get("ativo", True):
        return jsonify({"ativo": False, "mensagem": lic.get("mensagem", "Acesso suspenso pelo administrador.")}), 403

    return jsonify({"ativo": True, "mensagem": "OK", "expira_em": lic["expira_em"]})

# ROTAS PARA O PAINEL (ADMIN.HTML)
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
        "usuario_nome": data.get("nome", uid),
        "ativo": True,
        "expira_em": data_expira.isoformat(),
        "mensagem": "Licença ativa",
        "atualizado_em": datetime.now(timezone.utc).isoformat()
    }
    
    save_licencas(licencas)
    return jsonify({"status": "sucesso", "expira_em": data_expira.isoformat()})

@app.route('/admin/licencas/status', methods=['POST'])
def alterar_status():
    if request.headers.get("Authorization") != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    
    data = request.json
    uid = data.get("usuario_id")
    licencas = load_licencas()
    
    if uid in licencas:
        licencas[uid]["ativo"] = data.get("ativo", False)
        licencas[uid]["mensagem"] = data.get("mensagem", "Acesso bloqueado.")
        save_licencas(licencas)
        return jsonify({"status": "sucesso"})
    return jsonify({"erro": "Usuário não encontrado"}), 404

if __name__ == "__main__":
    # ESSENCIAL PARA O RENDER:
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)