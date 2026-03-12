# But what is a neural network? | Deep learning chapter 1

## Informações do vídeo

| Campo | Valor |
| --- | --- |
| **Canal** | [3Blue1Brown](https://www.youtube.com/channel/UCYO_jab_esuFRV4b17AJtAw) |
| **Data de publicação** | 05/10/2017 |
| **Duração** | 18min 40s |
| **Visualizações** | 22.2M visualizações |
| **Likes** | 526.7K |
| **URL** | https://www.youtube.com/watch?v=aircAruvnKk |
| **Idioma original** | en |

**Categorias:** Education

## Descrição original

What are the neurons, why are there layers, and what is the math underlying it?
Help fund future projects: https://www.patreon.com/3blue1brown
Written/interactive form of this series: https://www.3blue1brown.com/topics/neural-networks

Additional funding for this project was provided by Amplify Partners

For those who want to learn more, I highly recommend the book by Michael Nielsen that introduces neural networks and deep learning: https://goo.gl/Zmczdy

There are two neat things about this book.  First, it's available for free, so consider joining me in making a donation to Nielsen if you get something out of it.  And second, it's centered around walking through some code and data, which you can download yourself, and which covers the same example that I introduced in this video.  Yay for active learning!
https://github.com/mnielsen/neural-networks-and-deep-learning

I also highly recommend Chris Olah's blog: http://colah.github.io/

For more videos, Welch Labs also has some great series on machine learning: 
https://youtu.be/i8D90DkCLhI
https://youtu.be/bxe2T-V8XRs

For those of you looking to go *even* deeper, check out the text "Deep Learning" by Goodfellow, Bengio, and Courville.  

Also, the publication Distill is just utterly beautiful: https://distill.pub/

Lion photo by Kevin Pluck

Звуковая дорожка на русском языке: Влад Бурмистров.

Thanks to these viewers for their contributions to translations
German: @fpgro
Hebrew: Omer Tuchfeld
Hungarian: Máté Kaszap
Italian: @teobucci, Teo Bucci

-----------------
Timeline: 
0:00 - Introduction example
1:07 - Series preview
2:42 - What are neurons?
3:35 - Introducing layers
5:31 - Why layers?
8:38 - Edge detection example
11:34 - Counting weights and biases
12:30 - How learning relates
13:26 - Notation and linear algebra
15:17 - Recap
16:27 - Some final words
17:03 - ReLU vs Sigmoid

Correction 14:45 - The final index on the bias vector should be "k"

------------------
Animations largely made using manim, a scrappy open source python library.  https://github.com/3b1b/manim

If you want to check it out, I feel compelled to warn you that it's not the most well-documented tool, and has many other quirks you might expect in a library someone wrote with only their own use in mind.

Music by Vincent Rubinetti.
Download the music on Bandcamp:
https://vincerubinetti.bandcamp.com/album/the-music-of-3blue1brown

Stream the music on Spotify:
https://open.spotify.com/album/1dVyjwS8FBqXhRunaG5W5u

If you want to contribute translated subtitles or to help review those that have already been made by others and need approval, you can click the gear icon in the video and go to subtitles/cc, then "add subtitles/cc".  I really appreciate those who do this, as it helps make the lessons accessible to more people.
------------------

3blue1brown is a channel about animating math, in all senses of the word animate.  And you know the drill with YouTube, if you want to stay posted on new videos, subscribe, and click the bell to receive notifications (if you're into that).

If you are new to this channel and want to see more, a good place to start is this playlist: http://3b1b.co/recommended

Various social media stuffs:
Website: https://www.3blue1brown.com
Twitter: https://twitter.com/3Blue1Brown
Patreon: https://patreon.com/3blue1brown
Facebook: https://www.facebook.com/3blue1brown
Reddit: https://www.reddit.com/r/3Blue1Brown

## Conteúdo do vídeo (transcrição)

*Fonte: Legendas manuais (pt)*

Isto é um três. Está escrito de forma desleixada
e renderizado a uma resolução extremamente baixa de 28 por 28 pixels. Mas o seu cérebro não tem dificuldade
para reconhecê-lo como um três. E queria que você parasse para pensar em como é louco que cérebros
conseguem fazer isso sem esforço? Assim, isto, isto e isto também são
reconhecidos como três, ainda que os valores específicos de cada pixel
sejam bem diferentes em cada imagem. As células fotossensíveis no seu olho que
estão sendo ativadas quando você vê este três são bem diferentes daquelas que são
ativadas quando você vê este três; mas algo nesse seu córtex visual
louco de inteligente decide que elas
representam a mesma ideia, enquanto reconhece outras imagens
como ideias distintas.

Mas e se eu lhe dissesse para se sentar
e me escrever um programa que pega uma grade
de 28 por 28 pixels assim e emite um único número entre 0 e 10, que lhe diz qual ele acha
que é o dígito? Bom, a tarefa passa de comicamente fácil
para assustadoramente difícil. Se não tem vivido
embaixo de uma pedra, acho que mal preciso motivar
a relevância e importância do aprendizado de máquina
e redes neurais para o presente e o futuro. Mas aqui eu quero lhe mostrar
o que é uma rede neural de verdade, presumindo nenhum conhecimento, e ajudar a visualizar como ela funciona, não como uma palavra da moda,
mas como parte da matemática.

Espero que você saia sentindo
que a própria estrutura faz sentido e que sabe o que significa quando lê ou ouve
que uma rede neural "aprende". Este vídeo só vai focar
nos componentes estruturais disso e o próximo vai lidar
com o aprendizado. Vamos montar uma rede neural
capaz de aprender a reconhecer dígitos manuscritos. Este é um exemplo clássico
para apresentar o tópico. E fico feliz em me ater ao status quo aqui,
porque no fim dos dois vídeos, quero lhe indicar umas boas fontes
onde você pode aprender mais, e baixar o código que faz isto,
e brincar com ele no seu computador.

Há muitas variações de redes neurais, e nos últimos anos, houve uma explosão
nas pesquisas sobre essas variações. mas nestes dois
vídeos introdutórios só vamos ver a forma
mais simples sem penduricalhos. Isso é como um pré-requisito para entender qualquer uma
das variações modernas mais poderosas. E acredite em mim, ainda há muita complexidade
para tentarmos entender. Mas mesmo nesta forma simples, ela pode aprender a reconhecer
dígitos manuscritos, o que é uma capacidade muito legal
para um computador.

E ao mesmo tempo, você verá como ela fica aquém
de algumas coisas que podemos esperar dela. Como o nome sugere, redes neurais
são inspiradas no cérebro. Mas vamos entender isso melhor. O que são os neurônios
e em que sentido eles estão conectados? Daqui em diante, quando eu digo neurônio, quero que só pense numa coisa
que contém um número, especificamente um número entre 0 e 1. Realmente não passa disso. Por exemplo, a rede começa
com um monte de neurônios correspondentes a cada um dos
28x28 pixels da imagem de entrada, que são 784 neurônios no total.

Cada um deles contém um número que representa
o valor no nível de cinza do pixel correspondente, variando de zero para pixels pretos
a 1 para pixels brancos. Este número dentro do neurônio
se chama  sua "ativação". E a imagem que você
deve ter em mente aqui é que cada neurônio está "aceso"
quando sua ativação é um número alto. então, todos estes 784 neurônios
compõem a primeira camada da nossa rede. Agora, saltando para a última camada, esta tem dez neurônios,
cada um representando um dos dígitos. A ativação nestes neurônios (novamente um número entre 0 e1) representa quanto o sistema acha que uma dada imagem
corresponde com um dado dígito.

Também há algumas camadas no meio,
chamadas camadas ocultas, que por enquanto devem ser
só um grande ponto de interrogação para como que será feito esse processo
de reconhecer dígitos. Nesta rede escolhi duas camadas ocultas,
cada qual com 16 neurônios, e admito que
é uma escolha arbitrária. Sendo honesto, escolhi duas camadas com base em
como quero motivar a estrutura daqui a pouco e 16, bem, foi um bom número
para encaixar na tela. Na prática, há muito espaço para experimentar
com esta estrutura específica.

Como a rede funciona? Ativações em uma camada
determinam as ativações na camada seguinte. E, claro, o âmago da rede como um mecanismo
de processamento de informação, se resume a exatamente como as ativações
em uma camada provocam ativações na camada seguinte. É para ser, grosso modo, análogo a como,
em redes biológicas de neurônios, a ativação de alguns grupos de neurônios
causa a ativação de outros grupos. Ora, a rede que estou mostrando aqui
já foi treinada para reconhecer dígitos, e deixe-me mostrar
o que quero dizer com isso.

Significa que, se você insere uma imagem que acende todos os 784 neurônios
da camada de entrada de acordo com o brilho
de cada pixel da imagem, esse padrão de ativação causa
um padrão bem específico na camada seguinte, que causa um padrão específico
na seguinte, que finalmente produz um padrão
na camada de saída. E o neurônio mais brilhante dessa camada de saída é a escolha da rede, por assim dizer,
sobre qual dígito a imagem representa. E antes de entrar na matemática
de como uma camada influencia a seguinte, ou de como o treinamento
funciona, vamos falar de por que faz sentido esperar
que uma estrutura com camadas assim se comporte de forma inteligente.

O que esperamos aqui? O que é o melhor que podemos esperar
que as camadas ocultas estejam fazendo? Bem, quando você ou eu reconhecemos dígitos,
juntamos vários componentes. Um nove tem um círculo em cima
e uma linha na direita. Um oito também tem um circulo em cima,
mas é pareado com outro círculo embaixo. Um quatro basicamente se decompõe em 3 linhas,
etc. Ora, num mundo perfeito, podemos esperar que
cada neurônio na penúltima camada corresponda a
um desses subcomponentes, que sempre que você insira uma imagem,
digamos, com um círculo em cima, como um 9 ou um 8, haja algum neurônio específico
cuja ativação vá ser próxima a um.

E não quero dizer este círculo específico de pixels. A esperança é que qualquer padrão
circular geral no topo ative este neurônio. Assim, para ir
da terceira camada até a última, só é preciso aprender qual combinação de
subcomponentes corresponde a quais dígitos. Claro, isso só adia o problema, pois como você reconheceria
esses subcomponentes ou sequer aprenderia quais devem ser
os  subcomponentes corretos? E eu ainda nem falei de como
uma camada influencia a seguinte, mas continue comigo nisso
por um momento.

O reconhecimento de um círculo
também pode se decompor em subproblemas. Uma maneira razoável de fazer isso seria primeiro
reconhecer as várias pequenas bordas que o compõem. Da mesma forma, uma longa linha,
como você pode ver nos dígitos 1, 4 ou 7, isso é só uma longa borda. Ou você pode pensar nela como
certo padrão de várias bordas menores. Então, talvez esperemos que cada
neurônio na segunda camada da rede corresponda
às várias bordinhas relevantes. Talvez, quando uma imagem assim aparece, ela acenda todos os neurônios associados
com cerca de oito a dez bordinhas específicas, que, por sua vez, acendem os neurônios associados
com o círculo de cima e a longa linha vertical, e eles acendem
o neurônio associado com o nove.

Se isso é ou não é
o que a nossa rede realmente faz é outra questão, e voltaremos a ela quando virmos
como treinar a rede. Mas isso é algo
que podemos esperar, um tipo de objetivo
com a camada estruturada assim. Além do mais, você pode imaginar
como poder detectar bordas e padrões assim seria muito útil para outras tarefas
de reconhecimento de imagem. E mesmo além do reconhecimento de imagem há vários tipos de coisa inteligentes
que você pode querer fazer que se decompõem
em camadas de abstração. A análise sintática, por exemplo, envolve
a captura de áudio bruto e a extração de sons distintos, que combinam para formar certas sílabas, que combinam
para formar palavras, que combinam para formar expressões
e pensamentos mais abstratos, etc.

Mas voltando para como isso realmente funciona, imagine-se projetando o modo como
as ativações numa camada podem determinar
as ativações da seguinte. O objetivo é ter algum mecanismo
capaz de combinar pixels em bordas, ou bordas em padrões, ou padrões em dígitos. E focando num exemplo
bem específico, digamos que esperamos que um neurônio
em particular na segunda camada detecte se a imagem tem ou não
uma borda nesta região aqui. A questão em mãos é:
quais parâmetros a rede neural deve ter? Em que discadores e botões você deve poder mexer de modo que ela seja expressiva o bastante
para poder capturar este padrão?

Ou qualquer outro padrão de pixels? Ou o padrão de que várias bordas
podem fazer um círculo, e coisas assim? Bem, atribuiremos um peso a cada uma das conexões
entre nosso neurônio e os da primeira camada. Esses pesos são só números. Então pegue todas aquelas ativações
da primeira camada e calcule a sua soma ponderada
segundo o valor desses pesos. Acho útil conceber esses pesos como
organizados numa pequena grade deles próprios. E vou usar pixels verdes para indicar pesos positivos
e vermelhos para indicar pesos negativos, sendo o brilho de cada pixel
uma representação aproximada do valor do peso.

Ora, se definirmos como zero os pesos associados
com praticamente todos os pixels, exceto alguns pesos positivos
nesta região que nos importa, então, obter a soma ponderada
de todos os valores de pixels realmente se resume somar os valores
dos pixels só na região que nos importa. E, se você realmente deseja detectar
se existe uma borda aqui, você pode ter alguns pesos negativos
associados com os pixels ao redor. Então, a soma é maior
quando esses pixels do meio são brilhantes, mas os pixels ao redor são mais escuros.

Quando se calcula uma soma ponderada assim,
pode dar qualquer número. Mas para esta rede, queremos que
as ativações sejam algum valor entre 0 e1. Então, algo comum é introduzir
esta soma ponderada em alguma função que comprime
a reta de números reais num intervalo entre 0 e 1. E uma função comum que faz isso
se chama função sigmoide, também conhecida
como curva logística. Basicamente, entradas muito negativas
terminam próximas de zero e entradas muito positivas
terminam próximas de 1, e aumentam de forma constante
perto da entrada 0.

Então, a ativação do neurônio aqui é
basicamente uma medida de quão positiva
é a soma ponderada relevante. Mas talvez você não queira que o neurônio acenda
quando a soma ponderada passa de 0; talvez você só queira que ele se ative
quando a soma passa de, digamos, 10. Ou seja, você quer um viés para a inatividade. Então, só vamos acrescentar
outro número (como -10) a essa soma ponderada antes de inseri-la
na função sigmoide. Esse número adicional
se chama viés. Então, os pesos lhe dizem que padrão de pixel
este neurônio na segunda chamada está detectando, e o viés lhe diz quão alta
a soma ponderada precisa ser para o neurônio começar
a se ativar significativamente.

E isso é só um neurônio! Cada neurônio nesta camada estará conectado
a todos os 784 neurônios de pixel da primeira camada, e cada uma dessas 784 conexões
tem o seu próprio peso associado consigo. Além disso, cada um tem um viés, outro número adicionado à soma ponderada
antes de ser comprimido com a simoide. E isso é muita coisa para pensar. Com esta camada oculta de 16 neurônios,
é um total de 784x16 pesos junto com 16 vieses. E isso são só as conexões
entre a primeira camada e a segunda. As conexões entre as outras camadas
também têm um monte de pesos e vieses associados.

Ao todo, esta rede tem quase exatamente
13 mil pesos e vieses no total. 13 mil botões em que podemos mexer
para fazer esta rede se comportar de formas diferentes. Então,
quando falamos de aprendizado, isso se refere a fazer o computador achar
uma definição válida para todos esses vários números para que ele efetivamente resolva
o problema em questão. Um experimento mental que é
tanto divertido quanto horrível é se imaginar definindo todos
esses pesos e vieses à mão, ajustando de propósito os números
para que a segunda camada detecte bordas, a terceira camada detecte
padrões, etc.

Pessoalmente, acho
isso satisfatório, em vez de tratar a rede
como uma caixa-preta, porque quando a rede
não age como você espera, se você se familiarizou com
o significado desses pesos e vieses, você sabe onde começar
a mudar a estrutura para melhorá-la. Ou quando a rede funciona,
mas não pelas razões esperadas, captar o funcionamento dos pesos e vieses
é um bom modo de desafiar as suas suposições e expor o espaço completo
de soluções possíveis. Aliás, a função real aqui
é meio complicada de escrever, né?

Então, vou mostrar um jeito de representar essas conexões
que é mais compacto em termos notacionais. Você vai ver assim,
se ler mais sobre redes neurais. Organize todas as ativações de uma camada
numa coluna como um vetor. Então, organize todos os pesos
como uma matriz, sendo que cada fileira da matriz
corresponde às conexões entre uma camada e um neurônio específico
na camada seguinte. Isso significa que pegar a soma ponderada
das ativações da primeira camada, segundo esses pesos, corresponde a um dos termos
no produto matriz-vetor de tudo na esquerda aqui.

Aliás, muito do aprendizado de máquina se resume
a ter um bom entendimento de álgebra linear. Então, para os que desejam
um bom entendimento visual de matrizes e do que significa
a multiplicação de vetor e matriz, deem uma olhada na minha série
sobre álgebra linear, especialmente o capítulo 3. Voltando à nossa expressão, em vez de adicionar o viés
a cada um destes valores de modo independente, representamos organizando
todos esses vieses num vetor e adicionando o vetor inteiro
ao produtor vetor-matriz anterior.

Então, como etapa final, vou envolver tudo com uma sigmoide aqui. E isso representa a aplicação da função sigmoide
a cada componente específico do vetor resultante ali dentro. Então, depois de escrever esta matriz de pesos
e estes vetores como seus próprios símbolos, você pode comunicar toda a transição
de ativações de uma camada para a outra numa expressãozinha
extremamente organizada. E isso torna o código relevante mais simples e rápido, já que muitas bibliotecas
otimizam bastante a multiplicação de matrizes.

Lembra que disse que os neurônios
não passam de coisas que contêm números? Bem, claro que os números específicos
que eles contêm dependem da imagem inserida. Então, é mais preciso conceber
cada neurônio como uma função, que pega as saídas
de todos os neurônios da camada anterior e emite um número
entre 0 e 1. Na verdade, a rede inteira
não passa de uma função, que pega 784 números como entrada
e emite 10 números como saída. É uma função absurdamente complicada, que envolve 13 mil parâmetros na forma
desses pesos e vieses que captam certos padrões e que envolve a iteração de muitos produtos matriz-vetor
e a função sigmoide.

No entanto, é só uma função. E de certa forma, é reconfortante
que pareça complicada. Se fosse mais simples, como poderíamos
esperar que ela fosse capaz de reconhecer dígitos? Mas como ela é capaz disso? Como é que esta rede aprende
os pesos e vieses adequados só olhando os dados? Bom,
vou mostrar isso no próximo vídeo. Também vou me aprofundar no que
esta rede específica aqui está fazendo. Acho que agora eu tenho que dizer
para vocês se inscreverem para serem notificados
quando esse ou qualquer novo vídeo sair.

Mas, na realidade, a maioria de vocês
não recebe notificações do YouTube, né? Talvez seja mais honesto dizer: "Inscreva-se, para que as redes neurais
do algoritmo de recomendação do YouTube creiam que você deseja que
o conteúdo deste canal seja recomendado para você." Enfim, aguarde mais. Muito obrigado a todos que apoiam
estes vídeos no Patreon. Não progredi muito na série
sobre probabilidade este verão, mas vou voltar a ela depois deste projeto. Então, patrons,
podem procurar atualizações por lá. Para encerrar, aqui comigo
está Lisha Li, que fez doutorado sobre
o lado teórico do aprendizado profundo e trabalha atualmente
numa empresa de capital de risco chamada Amplify Partners, que gentilmente forneceu parte
do financiamento para este vídeo.

Então, Lisha, temos que mencionar
essa função sigmoide. Se bem entendo, redes mais antigas usavam isso
para comprimir a soma ponderada relevante naquele intervalo entre 0 e 1, e isso era motivado por uma analogia biológica
de neurônios estarem ativos ou inativos. Exato. Mas poucas redes modernas
continuam usando a sigmoide. Sim. É meio antiquada,
né? Ou melhor, a ReLu parece
muito mais fácil de treinar. E ReLu significa
"unidade linear retificada"? Sim, é uma função em que
pegamos um max, um 0 e a, sendo a dado pelo que
você explicou no vídeo.

E a motivação disso, em parte,
foi uma analogia biológica com a maneira como os neurônios
estão ativos ou não. Se passasse certo limiar,
seria a função de identidade. Se não, não seria ativado,
seria 0. Meio que uma simplificação. A sigmoide era muito difícil
de treinar em certo ponto, e experimentaram a ReLu e acabou funcionando muito bem
para redes neurais incrivelmente profundas. Certo! Obrigado, Lisha. Legendas: Luan Marques
(rmo.luan@gmail.com)

---
*Extraído em 12/02/2026 às 14:43 via youtube-extractor skill*