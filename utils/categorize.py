categories = {
    "Esporte": [
        "corrida", "futebol", "bike", "esporte", "atleta", "volei", "skate", "campeonato",
        "trilha", "ciclismo", "basquete", "esportiva", "open", "aberto", "maratona", "corrida de rua", "corrida de montanha", "ciclismo de estrada",
        "ciclismo mountain bike", "ciclismo de pista", "ciclismo BMX", "ciclismo de cicloturismo", "ciclismo de gravel", 
        "ciclismo de ciclocross", "ciclismo de pista", "ciclismo de estrada", "caminhada", "trilha", "trilheiros", "trilheiros e ciclistas",
        "trilheiros e caminhantes", "trilheiros e corredores", 
    ],
    "Teatro": [
        "peça", "drama", "ator", "palco", "teatro", "atriz", "espetáculo", "monólogo", 
        "encenação", "cena", "figurante", "dramaturgia", "teatral", "performance",
    ],
    "Shows e Festas": [
        "show", "música", "musica", "concerto", "banda", "pagode", "samba", "rock", "dj",
        "festival", "sertanejo", "dança", "bailão", "mpb", "funk", "eletrônica", "baile", "90's", "80's", "70's", "violão", 
        "orquestra", "sinfônica", "samba rock", "forró", "axé", "sertanejo", "violoncelo", "saxofone", "guitarra", "piano", "orquestra sinfônica"
        "Piano", "violino", "saxofone", "guitarra", "bateria", "percussão", "canto", "cantor", "cantora", "clássico", "clássico", 
        "sinfônico", "sinfônica", "orquestra sinfônica", "orquestra sinfônica", "forrozada", "forró", "forró eletrônico", 
        "forró pé de serra", "forró universitário", "forró tradicional", "bloco", "arraiá", "festa junina", "festa de São João", "festa julina", "gala", "bloco", 
        "fest", "notas", "sinfônica", "festa", "symphonic", "tribute", "tributo", "tenores", "tenor", "symphony", "symphonic orchestra", "flash back", "trio", 
        "vital", "acústico", "réveillon"
    ],
    "Comedy": [
        "stand up", "comédia", "humor", "piada", "comico", "engraçado", "risada", "humorista", "joker", "comediante", 
        "comedy", "standup", "stand-up", "stand up comedy", "standup comedy", "comédia stand up", "comédia standup", "paródia", "imitação", "improviso",
    ],
    "Gastronomia": [
        "gastronomia", "culinária", "comida", "boteco", "degustação", "vinho", "cozinha", "chef",
        "churrasco", "cerveja", "feira gastronômica", "comer", "boteco", "restaurante", "gastronomic", "gastronomic event", 
        "gastronomic festival", "botecão"
    ],
    "Evento Digital ou Online": [
        "podcast", "vídeo", "video", "entrevista", "audiovisual", "rádio", "online", "streaming",
        "sympla play", "transmissão", "plataforma", "evento online", "online", "ao vivo", "remoto", "streaming", "webinar"
    ],
    "Cursos e Workshops": [
        "curso", "workshop", "aula", "oficina", "treinamento", "capacitação", "mentoria", 
        "aprendizado", "formação", "certificação", "educação", "educacional", "educacional", "educacional",
        "educacional", "educacional", "educacional", "educacional", "tec", "tecnologia", "tecnológico", "tecnológica", 
    ],
    "Congressos e Palestras": [
        "palestra", "congresso", "debate", "seminário", "mesa redonda", "talk", "evento técnico", "encontro", "simpósio", "simposium", 
        "equipes", "produtividade","eficiência", "gestão", "liderança", "inovação", "tecnologia", "ciência", "pesquisa", "educação", "finacneira",
        "comunicação", "gestão", "aprender", "aprenda", "conversa"
    ],
    "Passeios e Tours": [
        "tour", "passeio", "visita guiada", "excursão", "trilha", "bike tour", "viagem", "esposição", "cidade"
    ],
    "Infantil": [
        "infantil", "criança", "kids", "palhaço", "desenho", "brinquedo", "família", "família"
    ],
    "Religião e Espiritualidade": [
        "religião", "espiritualidade", "oração", "retiro", "missa", "evangelho", "culto", "fé",
        "igreja", "avivação", "meditação", "espiritual", "espírita", "espiritualidade", "retiro espiritual", "frutificar", "culto de louvor", "culto de adoração"
        "deus", "Deus", "jesus", "jesus cristo", "espírito santo", "santo", "santa ceia", "oração", "oração de cura", "oração de libertação", 
        "IPB", "igreja", "evangelho", "evangelização", "missão", "missionário", "missionária", "missionários", "missionárias", "evangelista", 
        "evangelistas", "biblia", "bíblia", "bíblico", "bíblica", "escrituras", "escritura", "sagrado", "sagrada", "sagrado coração de jesus", 
        "sagrado coração de maria"
    ],
    "Pride": [
        "pride", "lgbt", "lgbtqia+", "diversidade", "parada", "orgulho", "inclusão"
    ],
    "Saúde e Bem-Estar": [
        "saúde", "bem-estar", "fitness", "meditação", "ioga", "pilates", "nutrição", 
        "autocuidado", "terapia", "psicologia", "psicólogo", "psicóloga", "psicoterapia", "terapia ocupacional", "acupuntura", "massagem", "relaxamento",
        "meditação guiada", "yoga", "ioga", "pilates",
    ],
    
}

def categorize_event(title):
    if not title:
        return "Outros"

    title_lower = title.lower()
    for category, keywords in categories.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "Outros"

