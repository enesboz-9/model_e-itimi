"""Rehber yazıları (elle yazılmış, genel bilgi). build_pages.py bunları /rehber/<slug> olarak üretir."""

YAZILAR = {
    "boyali-arac-fiyati": {
        "baslik": "Boyalı Araç Fiyatı Ne Kadar Düşürür? Boya, Değişen ve Hasar Kaydı",
        "aciklama": "Boyalı, lokal boyalı ve değişen parça ne demek? Hasar durumu ikinci el araç fiyatını nasıl etkiler, ekspertiz raporunda nelere bakılır?",
        "ozet": "Boyalı ve değişen parçalar ile hasar kaydının fiyata etkisi.",
        "html": """
<p>İkinci el araç ilanlarında en çok sorulan sorulardan biri, boyalı ya da değişen parçanın fiyatı ne kadar etkilediğidir. Kısa cevap: etki; parçaya, kaç parça olduğuna, aracın yaşına ve modeline göre ciddi biçimde değişir. Bu yüzden herkes için geçerli tek bir yüzde vermek yanıltıcı olur.</p>
<h2>Terimler ne anlama gelir?</h2>
<ul>
<li><b>Orijinal:</b> Parça fabrika boyasıyla duruyor, onarım görmemiş.</li>
<li><b>Lokal boyalı:</b> Parçanın yalnızca bir bölümü boyanmış (çizik, ezik onarımı gibi).</li>
<li><b>Boyalı:</b> Parça tamamen boyanmış; çoğunlukla küçük hasar ya da kozmetik nedenlerle yapılır.</li>
<li><b>Değişen:</b> Parça yenisiyle ya da başka bir parçayla değiştirilmiş.</li>
<li><b>Ağır hasar kayıtlı:</b> Araç sigorta/hasar sisteminde ağır hasarlı olarak kayda geçmiş. Bu, tek tek boyalı parçalardan farklı ve genellikle fiyatı daha çok etkileyen bir durumdur.</li>
</ul>
<h2>Fiyatı hangi durumlar daha çok etkiler?</h2>
<ul>
<li><b>Yapısal parçalar:</b> Tavan, direkler, şasi uçları ve podyeler gibi aracın taşıyıcı yapısıyla ilgili parçalardaki değişim ya da onarım, çamurluk veya kapı boyasından çok daha önemlidir; güvenlik ve sürüş davranışıyla ilgilidir.</li>
<li><b>Parça sayısı:</b> Tek bir kapı boyası ile birden fazla parçada boya ya da değişim aynı etkiyi yapmaz.</li>
<li><b>Araç yaşı ve segmenti:</b> Yeni ve pahalı araçlarda hasar geçmişi alıcı tarafından daha sıkı sorgulanır.</li>
<li><b>Belgelenebilirlik:</b> Onarımın nedeni, faturası ve ekspertiz raporu ile açıklanabiliyorsa pazarlıkta sizin için daha güçlü bir konum sağlar.</li>
</ul>
<h2>Satın alırken ne yapmalı?</h2>
<ol>
<li>İlandaki "boyasız" ya da "değişensiz" ifadesine güvenmeyin; <b>bağımsız bir ekspertiz</b> yaptırın.</li>
<li>Ekspertiz raporunda parça durumlarını tek tek inceleyin; özellikle tavan, direk ve şasi bölgelerine bakın. Raporu okumak için <a href="/rehber/ekspertiz-raporu-nasil-okunur">ekspertiz rehberine</a> göz atın.</li>
<li>Hasar kaydını resmi hasar sorgulama servisleri üzerinden kontrol edin.</li>
<li>Fiyatı, aynı model ve yıldaki benzer araçlarla karşılaştırın.</li>
</ol>
<h2>Kendi aracınız için deneyin</h2>
<p>EderiNe değerleme aracında parçaları araç şeması üzerinde <i>boyalı</i> ya da <i>değişen</i> olarak işaretleyip tahmini değerin nasıl değiştiğini görebilirsiniz. Bu, kesin bir fiyat değil, benzer ilanlara ve modele dayalı bir tahmindir.</p>
""",
    },
    "ekspertiz-raporu-nasil-okunur": {
        "baslik": "Ekspertiz Raporu Nasıl Okunur? Alıcı İçin Kısa Rehber",
        "aciklama": "İkinci el araç ekspertiz raporundaki bölümler ne anlama gelir? Kaporta, mekanik, motor ve alt takım bölümlerinde nelere dikkat edilmeli?",
        "ozet": "Ekspertiz raporundaki bölümler ve nelere dikkat edilmeli.",
        "html": """
<p>Ekspertiz raporu, ikinci el aracın durumunu bağımsız bir uzman gözüyle özetler. Rapor uzun ve teknik görünebilir; aşağıdaki başlıklara odaklanmak okumayı kolaylaştırır. Raporların biçimi firmadan firmaya değişir, bu yazı genel bir çerçeve sunar.</p>
<h2>1. Kaporta ve boya</h2>
<p>Her parça için orijinal, lokal boyalı, boyalı ya da değişen gibi bir durum yazar. İlandaki beyanla karşılaştırın. Özellikle tavan, direkler, şasi uçları ve podye gibi yapısal bölgelerdeki işlemler dikkat gerektirir. Ayrıntılı açıklama için <a href="/rehber/boyali-arac-fiyati">boyalı araç rehberine</a> bakın.</p>
<h2>2. Motor ve mekanik</h2>
<ul>
<li>Yağ, soğutma suyu ve diğer sıvılarda kaçak ya da sızıntı olup olmadığı,</li>
<li>Motor sesi, titreşim ve çalışma düzeni,</li>
<li>Şanzıman geçişleri (otomatik/yarı otomatik araçlarda sarsıntı veya gecikme).</li>
</ul>
<h2>3. Alt takım, fren ve lastik</h2>
<p>Z rotları, rotiller, amortisörler, fren balata ve diskleri ile lastik aşınması raporda yer alır. Bunlar sarf ve bakım kalemleridir; fiyat pazarlığında kullanılabilir ama bazıları güvenlikle de ilgilidir.</p>
<h2>4. Elektronik ve hata kodları</h2>
<p>Birçok raporda bilgisayarlı arıza tespiti (OBD) sonucu bulunur. Kayıtlı hata kodları varsa nedenini sorun ve çözümlenip çözümlenmediğini öğrenin.</p>
<h2>5. Kilometre ve geçmiş</h2>
<p>Kilometre tutarlılığı, bakım kayıtları ve hasar geçmişi birlikte değerlendirilmelidir. Rapordaki kilometre ile göstergeyi ve bakım belgelerini karşılaştırın.</p>
<h2>Raporu okurken akılda tutulacaklar</h2>
<ul>
<li>Raporun tarihine bakın; eski bir rapora güvenmeyin.</li>
<li>Ekspertizi satıcının değil, <b>kendi seçtiğiniz</b> bir firmanın yapması daha güvenilirdir.</li>
<li>Rapor, geleceğe dair garanti vermez; yalnızca o günkü durumu gösterir.</li>
<li>Anlamadığınız bir ifadeyi ekspertiz uzmanına sorun.</li>
</ul>
""",
    },
    "ikinci-el-arac-alirken-dikkat-edilecekler": {
        "baslik": "İkinci El Araç Alırken Dikkat Edilecekler: Kontrol Listesi",
        "aciklama": "İkinci el araç alırken hasar kaydı, ekspertiz, noter satışı ve fiyat karşılaştırması dahil adım adım kontrol listesi.",
        "ozet": "Satın almadan önce adım adım kontrol listesi.",
        "html": """
<p>İkinci el araç alımı büyük bir harcamadır ve sonradan düzeltmesi zor hatalar yapılabilir. Aşağıdaki liste, satın almadan önce sırayla kontrol edebileceğiniz başlıkları özetler. Mevzuat ve uygulamalar değişebildiği için resmî adımları güncel kaynaklardan da doğrulayın.</p>
<h2>1. Fiyatı araştırın</h2>
<p>Aynı marka, model, yıl ve benzer kilometredeki ilanları karşılaştırın. <a href="/ikinci-el-arac-fiyatlari">Fiyat sayfalarımızdan</a> ya da <a href="/arac-degerleme">değerleme aracından</a> yararlanabilirsiniz. Piyasanın belirgin biçimde altındaki fiyatlar dikkat gerektirir.</p>
<h2>2. Araç geçmişini sorgulayın</h2>
<ul>
<li>Hasar kaydı ve ağır hasar durumu,</li>
<li>Kilometre ve bakım geçmişinin tutarlılığı,</li>
<li>Ruhsat bilgileri ile şasi numarasının araçtakiyle uyumu,</li>
<li>Rehin, haciz ve vergi/ceza borçlarının olup olmadığı.</li>
</ul>
<h2>3. Ekspertiz yaptırın</h2>
<p>Kendi seçtiğiniz bağımsız bir ekspertiz firmasına rapor hazırlatın. Raporu anlamak için <a href="/rehber/ekspertiz-raporu-nasil-okunur">ekspertiz rehberine</a> bakın.</p>
<h2>4. Test sürüşü yapın</h2>
<p>Farklı hızlarda ve yol koşullarında deneyin; direksiyon, fren, vites ve alt takımdan gelen seslere dikkat edin. Soğuk motorla ilk çalıştırmayı görmek faydalıdır.</p>
<h2>5. Belgeleri kontrol edin</h2>
<p>Ruhsat, kimlik, servis ve bakım faturaları, ikinci anahtar ve garanti belgelerini isteyin. Satıcının aracın sahibi olduğundan emin olun.</p>
<h2>6. Pazarlık ve ödeme</h2>
<ul>
<li>Ekspertizde çıkan kusurları pazarlıkta gerekçe olarak kullanın.</li>
<li>Ödemeyi izlenebilir bir yolla (banka transferi gibi) ve satış işlemiyle eş zamanlı yapın; nakit taşımaktan kaçının.</li>
<li>Satış işlemini yetkili merciler (noter) üzerinden yapın ve belgeleri saklayın.</li>
</ul>
<h2>7. Satın aldıktan sonra</h2>
<p>Sigorta, muayene ve bakım durumunu gözden geçirin; yağ ve filtre gibi kalemleri ilk fırsatta yenilemek iyi bir başlangıçtır.</p>
""",
    },
}
