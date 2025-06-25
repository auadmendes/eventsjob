categories = {
    "Esporte": [
        "corrida", "futebol", "bike", "esporte", "atleta", "volei", "skate", "campeonato",
        "trilha", "ciclismo", "basquete", "esportiva"
    ],
    "Teatro": [
        "peça", "drama", "ator", "palco", "teatro", "atriz", "espetáculo", "monólogo", 
        "encenação", "cena"
    ],
    "Música": [
        "show", "música", "musica", "concerto", "banda", "pagode", "samba", "rock", "dj",
        "festival", "sertanejo", "dança", "bailão", "mpb", "funk", "eletrônica"
    ],
    "Stand Up Comedy": [
        "stand up", "comédia", "humor", "piada", "comico", "engraçado", "risada", "humorista"
    ],
    "Gastronomia": [
        "gastronomia", "culinária", "comida", "boteco", "degustação", "vinho", "cozinha", "chef",
        "churrasco", "cerveja", "feira gastronômica"
    ],
    "Digital": [
        "podcast", "vídeo", "video", "entrevista", "audiovisual", "rádio", "online", "streaming",
        "sympla play", "transmissão", "plataforma"
    ],
    "Cursos e Workshops": [
        "curso", "workshop", "aula", "oficina", "treinamento", "capacitação", "mentoria", 
        "aprendizado", "formação"
    ],
    "Congressos e Palestras": [
        "palestra", "congresso", "debate", "seminário", "mesa redonda", "talk", "evento técnico"
    ],
    "Passeios e Tours": [
        "tour", "passeio", "visita guiada", "excursão", "trilha", "bike tour", "viagem"
    ],
    "Infantil": [
        "infantil", "criança", "kids", "palhaço", "desenho", "brinquedo", "família", "família"
    ],
    "Religião e Espiritualidade": [
        "religião", "espiritualidade", "oração", "retiro", "missa", "evangelho", "culto", "fé",
        "igreja"
    ],
    "Pride": [
        "pride", "lgbt", "lgbtqia+", "diversidade", "parada", "orgulho", "inclusão"
    ],
    "Eventos Online": [
        "evento online", "online", "ao vivo", "remoto", "streaming", "webinar"
    ]
}

def categorize_event(title):
    if not title:
        return "Outros"

    title_lower = title.lower()
    for category, keywords in categories.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "Outros"
