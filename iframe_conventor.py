h = open('embedded_index.html', encoding='utf-8').read()
e = h.replace('&', '&amp;').replace('"', '&quot;')
open('iframe_embedded.html', 'w', encoding='utf-8').write(
    f'<iframe allow="camera; microphone; autoplay" allowfullscreen '
    f'style="width:100%;height:100vh;border:0;" srcdoc="{e}"></iframe>')