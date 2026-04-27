import secrets # Para gerar a senha automática
import string

@app.route('/admin/licencas/gerar', methods=['POST'])
def gerar():
    if request.headers.get("Authorization") != ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 401
    
    data = request.json
    nome = data.get("nome")
    email = data.get("email") # Usaremos o e-mail como ID único
    dias = int(data.get("dias", 30))

    # Gera uma senha automática de 8 caracteres (letras e números)
    caracteres = string.ascii_uppercase + string.digits
    senha_gerada = ''.join(secrets.choice(caracteres) for i in range(8))

    licencas = load_licencas()
    data_expira = (datetime.now(timezone.utc) + timedelta(days=dias))
    
    licencas[email] = {
        "nome": nome,
        "email": email,
        "chave": senha_gerada, # Esta é a senha que o cliente vai usar
        "ativo": True,
        "expira_em": data_expira.isoformat()
    }
    
    save_licencas(licencas)
    return jsonify({"status": "sucesso", "senha": senha_gerada})
