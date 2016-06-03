library(tidyr)
library(dplyr)
library(pwr)
library(rjson)
library(ggplot2)
library(ggthemes)
library(entropy)
library(bootstrap)
theme_new <- theme_set(theme_few(base_size=22, base_family='serif'))

# for bootstrapping 95% confidence intervals
theta <- function(x,xdata) {mean(xdata[x], na.rm=T)}
ci.low <- function(x) {
  quantile(bootstrap::bootstrap(1:length(x),1000,theta,x)$thetastar,.025)}
ci.high <- function(x) {
  quantile(bootstrap::bootstrap(1:length(x),1000,theta,x)$thetastar,.975)}

################## basic design/participants stuff ########################

demographics.et.al = read.csv('data/anonymized-results.csv')
demographics.summary = demographics.et.al %>%
  group_by(workerid, condition, age, comments, education, language,
           ethnicity, gender, languageFree, studyQuestionGuess) %>%
  summarise() %>% as.data.frame()
print(paste('nsubj:', nrow(demographics.summary)))
print(paste('non-native english speakers:', nrow(demographics.summary %>% filter(language=='other'))))

design.stats = function(df, variable) {
  df$N = df[[variable]]
  stats = df %>% summarise(mean=mean(N),
                           min=min(N),
                           max=max(N), 
                           sd=sd(N), 
                           quant95low=quantile(N,0.025), 
                           quant95high=quantile(N,0.975))
  return(stats)
}
tasks.design = demographics.et.al %>%
  group_by(document) %>%
  summarise(nchains=length(unique(chain)),
            ncloze=length(unique(paste(chain, clozeIndex)))) %>% as.data.frame()
print(paste('ndocs:', nrow(tasks.design)))
nchains.per.doc.stats = design.stats(tasks.design, 'nchains')
ncloze.per.doc.stats = design.stats(tasks.design, 'ncloze')
print(paste('chains per doc:', nchains.per.doc.stats$min, '-', nchains.per.doc.stats$max))
print(paste('cloze per doc:', ncloze.per.doc.stats$min, '-', ncloze.per.doc.stats$max))

full.design = demographics.et.al %>%
  group_by(document, chain, clozeIndex, condition) %>%
  summarise(N=length(condition)) %>% as.data.frame()
nsubj.per.cond.stats = design.stats(full.design, 'N')
ncloze = length(unique(with(demographics.et.al, paste(document, chain, clozeIndex))))
print(paste('n cloze tasks:', ncloze))
print(paste('n cloze task X condition:', ncloze*3))
print(paste('tasks with at least one response:', nrow(full.design %>% filter(N>1))))

################## human cloze task performance ########################

automatic.cloze.data = read.table('data/verb-processed-data.txt', sep=' ',
                                  col.names=c('doc', 'chain', 'cloze', 'cond', 'prop.match.orig',
                                              'prop.match.mode', 'n.match.mode', 'n', 'mode', 'loosely.orig', 'orig', 'n.loose.mode')) %>%
  mutate(prop.loosely.match = loosely.orig/n,
         cond = factor(cond, levels=c('event_only', 'caveman', 'original')),
         tag = paste(doc, chain, cloze, cond)) %>%
  rename(document=doc, clozeIndex=cloze, condition=cond, prop.match=prop.loosely.match) %>%
  select(document, chain, clozeIndex, prop.match, condition) %>%
  mutate(matching.method='Automatic Matching')
manual.cloze.data = read.csv('data/experiment3-annotated.csv')
manual.cloze.data.by.task = manual.cloze.data %>%
  group_by(document, chain, clozeIndex, condition) %>% 
  summarise(prop.match = mean(vpmatch=='yes')) %>%
  mutate(matching.method='Manual Matching') %>% as.data.frame
cloze.df = rbind(automatic.cloze.data, manual.cloze.data.by.task)
cloze.df %>%
  mutate(condition=factor(condition, levels=c('event_only', 'caveman', 'original'), labels=c('Event Only', 'Caveman', 'Original'))) %>%
  group_by(matching.method, condition) %>%
  summarise(low = ci.low(prop.match),
            high= ci.high(prop.match),
            prop.match = mean(prop.match, na.rm=T)) %>%
  ggplot(., aes(x=condition, y=prop.match, fill=condition)) +
  geom_bar(stat='identity') +
  geom_errorbar(aes(x=condition, ymin=low, ymax=high), width=0.01) +
  facet_wrap(~matching.method) +
  scale_fill_few() +
  ylab('Performance') +
  xlab('Linguistic Condition') +
  ylim(0, 1)
ggsave('../paper/images/human-cloze.png', width=10, height=4)
## is condition a significant predictor of performance?
## stats for auto matching
## stats for manual matching
## original is last, so we're comparing original to the other two in the second comparison
auto.cloze = automatic.cloze.data %>%
  mutate(tag=paste(document, chain, clozeIndex)) %>%
  select(tag, condition, prop.match)
print(paste('with automatic tagging, average performance:', signif(mean(auto.cloze$prop.match), 2)))
orig.better.auto = summary(lm(prop.match ~ condition, data=auto.cloze, contrasts=list(condition='contr.helmert')))
print('with automatic tagging, original condition is not significantly better than the other two:')
print(coef(orig.better.auto)['condition2',])
print(paste('degrees of freedom:', paste(orig.better.auto$df[1:2], collapse=',')))

manual.cloze = manual.cloze.data.by.task %>%
  mutate(tag=paste(document, chain, clozeIndex)) %>%
  select(tag, condition, prop.match)
orig.better.manual = summary(lm(prop.match ~ condition, data=manual.cloze, contrasts=list(condition='contr.helmert')))
print('with manual tagging, original condition is better than the other two:')
print(coef(orig.better.manual)['condition2',])
## answer: yes, original is better, but people stick suck
print(paste('with manual tagging, average performance:', signif(mean(manual.cloze$prop.match, na.rm=T),2)))
print(paste('degrees of freedom:', paste(orig.better.manual$df[1:2], collapse=',')))

################## human cloze task agreement ########################

verb.data = read.csv('data/experiment3-with-main-verbs.csv') %>%
  mutate(synset = as.character(synset),
         root.predicate = as.character(root.predicate),
         synset=factor(synset, levels=names(table(synset))[rev(order(table(synset)))]),
         tag = paste(document, chain, clozeIndex)) %>%
  select(tag, condition, synset, vp) %>%
  rename(manual.gloss = vp,
         automatic.gloss = synset) %>%
  gather(method, gloss, 3:4) %>%
  separate(method, into=c('method', 'trash')) %>% select(-trash) %>%
  mutate(method=factor(method)) %>%
  as.data.frame

agreement = verb.data %>%
  group_by(tag, condition, method) %>%
  summarise(max.possible.entropy = log(length(tag)),
            ### to do: bootstrap correction!!!
            entropy = entropy(table(gloss))) %>%
  filter(max.possible.entropy > 0) %>%
  mutate(agreement = 1 - (entropy/max.possible.entropy))  %>%
  as.data.frame

agreement %>%
  group_by(method, condition) %>%
  summarise(low = ci.low(agreement),
            high = ci.high(agreement),
            agreement = mean(agreement)) %>%
  ggplot(., aes(x=condition, y=agreement, fill=condition)) +
  geom_bar(stat='identity') +
  facet_wrap(~method) +
  geom_errorbar(aes(x=condition, ymin=low, ymax=high), width=0.01) +
  ylim(0, 1) +
  scale_fill_few() +
  ylab('Agreement') +
  xlab('Linguistic Condition') +
ggsave('../paper/images/human-agreement.png', width=10, height=4)

agreement.stats = function(this.method) {
  agree = agreement %>% filter(method==this.method) %>%
    select(tag, condition, agreement)
  agree.fit = summary(lm(agreement ~ condition, data=agree, contrasts=list(condition='contr.helmert')))
  print(paste('with ', this.method, ' tagging, original condition is no better than the other two:'))
  print(coef(agree.fit)['condition2',])
  ## answer: yes, original is better, but people stick suck
  print(paste('with ', this.method, ' tagging, average agreement:', signif(mean(agree$agreement, na.rm=T),2)))
  print(paste('degrees of freedom:', paste(agree.fit$df[1:2], collapse=',')))
}
agreement.stats('manual')
agreement.stats('automatic')

################## human and model comparison ########################

aggr.agreement = agreement %>% group_by(tag) %>% summarise(agreement = mean(agreement))
agreement = aggr.agreement$agreement
names(agreement) = aggr.agreement$tag
pmi = read.csv('data/pmi-model-rankings.csv')
comparison = pmi %>%
  filter(exactness=='syns') %>%
  mutate(tag = paste(document, chain, cloze),
         ranking = ifelse(ranking<100, ranking, 100),
         source = factor(source,
                         levels=c('actual', 'response'),
                         labels=c('Actual Verbs', 'Response Verbs'))) %>%
  group_by(document, chain, cloze, exactness, source) %>%
  summarise(min.rank = min(ranking),
            mean.rank = mean(ranking),
            prop.rankings.in.top.50 = mean(ranking < 50),
            human.agreement = agreement[tag[1]]) %>%
  as.data.frame
ggplot(comparison, aes(x=human.agreement, y=min.rank, colour=source)) +
  geom_point(size=4, alpha=0.3) +
  facet_grid(~source) +
  xlab("Participants' Agreement") +
  ylab("Model's Best Rank") +
  scale_colour_few()
ggsave('../paper/images/human-model-comparison.png', width=10, height=4)

print('human agreement is not correlated with model responses')
print(with(comparison, cor.test(min.rank, human.agreement)))
print(with(comparison %>% filter(min.rank<100), cor.test(min.rank, human.agreement)))