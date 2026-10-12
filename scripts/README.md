# Painel de atividade

Execute `python scripts/update_profile_stats.py`. Apenas a biblioteca padrão é necessária. O workflow atualiza diariamente às 07:17 UTC e também aceita execução manual.

A fonte é o calendário publicamente visível de EDY075 no GitHub. Contribuições incluem mais ações que commits e podem incluir contagens privadas anonimizadas conforme a preferência do perfil. As seis métricas usam o período completo informado no rodapé. A sequência atual admite que hoje ainda não terminou, mas não ignora outros dias sem atividade. A média divide o total pelos dias com atividade. O gráfico mostra os últimos seis meses disponíveis; o último é parcial.

Contagens ausentes, datas descontínuas e divergência do cabeçalho interrompem a atualização, preservando o último painel válido. A imagem SVG só usa animação visual de entrada, sem JavaScript nem serviços externos de estatísticas.

Verificação: `python -m unittest discover -s scripts -p 'test_*.py'`.
