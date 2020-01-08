# myprojects

artical_similaer文章相似度比较,主要利用gensim
训练语料的预处理指的是将文档中原始的字符文本转换成Gensim模型所能理解的稀疏向量的过程。
通常，我们要处理的原生语料是一堆文档的集合，每一篇文档又是一些原生字符的集合。在交给Gensim的模型训练之前，我们需要将这些原生字符解析成Gensim能处理的稀疏向量的格式。由于语言和应用的多样性，我们需要先对原始的文本进行分词、去除停用词等操作，得到每一篇文档的特征列表。例如，在词袋模型中，文档的特征就是其包含的word
接下来，我们可以调用Gensim提供的API建立语料特征（此处即是word）的索引字典，并将文本特征的原始表达转化成词袋模型对应的稀疏向量的表达。
到这里，训练语料的预处理工作就完成了。我们得到了语料中每一篇文档对应的稀疏向量（这里是bow向量）；向量的每一个元素代表了一个word在这篇文档中出现的次数。
最后，出于内存优化的考虑，Gensim支持文档的流式处理
对文本向量的变换是Gensim的核心。通过挖掘语料中隐藏的语义结构特征，我们最终可以变换出一个简洁高效的文本向量。
在Gensim中，每一个向量变换的操作都对应着一个主题模型
首先是模型对象的初始化。通常，Gensim模型都接受一段训练语料（注意在Gensim中，语料对应着一个稀疏向量的迭代器）作为初始化的参数。显然，越复杂的模型需要配置的参数越多。
其中，corpus是一个返回bow向量的迭代器。这两行代码将完成对corpus中出现的每一个特征的IDF值的统计工作。
接下来，我们可以调用这个模型将任意一段语料（依然是bow向量的迭代器）转化成TFIDF向量（的迭代器）。需要注意的是，这里的bow向量必须与训练语料的bow向量共享同一个特征字典（即共享同一个向量空间）。
Gensim内置了多种主题模型的向量变换，包括LDA，LSI，RP，HDP等。这些模型通常以bow向量或tfidf向量的语料为输入，生成相应的主题向量。所有的模型都支持流式计算。
在得到每一篇文档对应的主题向量后，我们就可以计算文档之间的相似度，进而完成如文本聚类、信息检索之类的任务。在Gensim中，也提供了这一类任务的API接口。
首先，我们需要将待检索的query和文本放在同一个向量空间里进行表达（以LSI向量空间为例）：
lsi_model = models.LsiModel(corpus, id2word=dictionary,num_topics=2)
documents = lsi_model[corpus]
query_vec = lsi_model[query]
接下来，我们用待检索的文档向量初始化一个相似度计算的对象：
index = similarities.MatrixSimilarity(documents)
我们也可以通过save()和load()方法持久化这个相似度矩阵：
index.save('/tmp/test.index')
index = similarities.MatrixSimilarity.load('/tmp/test.index')
注意，如果待检索的目标文档过多，使用similarities.MatrixSimilarity类往往会带来内存不够用的问题。此时，可以改用similarities.Similarity类。二者的接口基本保持一致。
最后，我们借助index对象计算任意一段query和所有文档的（余弦）相似度：
sims = index[query_vec] 
#返回一个元组类型的迭代器：(idx, sim)
