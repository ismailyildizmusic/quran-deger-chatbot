VALUES = {
    "Adalet": [
        "adalet", "haksız", "zulüm", "eşit", "tarafsız", "hak", "ayrımcılık",
        "torpil", "kayırma", "hakkaniyet"
    ],
    "Kul hakkı": [
        "kul hakkı", "hakkını", "emeğini yemek", "gasbet", "emanet", "borç",
        "aldım vermedim", "haksız kazanç"
    ],
    "Doğruluk": [
        "yalan", "dürüst", "doğru", "hile", "aldat", "iftira", "yanlış bilgi",
        "kandır", "sahte"
    ],
    "Mahremiyet": [
        "mahrem", "izinsiz", "fotoğraf", "video", "paylaş", "ifşa", "gizli",
        "özel", "dm", "ekran görüntüsü", "dedikodu", "gıybet"
    ],
    "Güven": [
        "güven", "sır", "ihanet", "sadakat", "söz", "vaat", "emanet", "arkadan iş",
        "güven kırmak"
    ],
    "Emek": [
        "emek", "kopya", "intihal", "çalıntı", "hak etmek", "çalışmak",
        "başkasının ödevi", "hazıra konmak"
    ],
    "İsraf": [
        "israf", "boşa", "savurgan", "gereksiz", "tüketim", "nimet",
        "çöpe atmak", "fazla harcama"
    ],
}

# Arama için “tohum” kelimeler (API search'e gidecek)
SEARCH_SEEDS = {
    "Adalet": ["adalet", "zulüm", "hak"],
    "Kul hakkı": ["hak", "emanet", "haksız"],
    "Doğruluk": ["yalan", "iftira", "dürüst"],
    "Mahremiyet": ["zan", "gıybet", "dedikodu"],
    "Güven": ["emanet", "ahd", "söz"],
    "Emek": ["emek", "haksız", "kopya"],
    "İsraf": ["israf", "savurgan", "nimet"],
}

# Basit stopword listesi (çok kaba, yeter)
STOPWORDS_TR = {
    "ve", "veya", "ile", "ama", "fakat", "ancak", "de", "da", "ki", "bu", "şu",
    "bir", "ben", "sen", "o", "biz", "siz", "onlar", "mi", "mı", "mu", "mü",
    "için", "gibi", "çok", "az", "daha", "en", "ne", "nasıl", "neden"
}
