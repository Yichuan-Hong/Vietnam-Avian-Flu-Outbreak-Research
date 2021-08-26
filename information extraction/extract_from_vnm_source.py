#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import re
import sys

location_keywords = ['làng', 'thôn', 'xã', 'thương', 'huyện', 'vụ', 'tỉnh', 'tỉnh thành', 'quận', 'thành phố']
action_keywords = ['phát hiện', 'tìm thấy', 'tìm ra', 'nhận thấy', 'báo cáo', 'tường thuật', 'tuyên bố', 'khai báo', 'thông báo']

def get_article_data(news_source):
    articles = pd.read_csv('data/' + news_source + '_articles_vietnamese.csv')
    articles['Date'] = pd.to_datetime(articles['Date'])
    articles['Content'] = articles['Content'].astype(str)
    articles['Content'] = [text.strip().lower() for text in articles['Content']]

    return articles

def get_location_names():
    provinces = open('data/provinces.txt', 'r').read().split('\n')[:-1]
    cities = open('data/cities.txt', 'r').read().split('\n')[:-1]
    districts = open('data/districts.txt', 'r').read().split('\n')[:-1]
    westernized_districts = open('data/westernized_districts.txt', 'r').read().split('\n')[:-1]
    locations = [p.lower() for p in provinces] + [c.lower() for c in cities] + [d.lower() for d in districts] + [d.lower() for d in westernized_districts]

    return locations

def main(news_source):
    # get article and location data
    articles = get_article_data(news_source)
    locations = get_location_names()

    initial_filter = [(('cúm gia cầm' in text) or ('bùng phát' in text) or ('dịch' in text) or (len(re.findall('H\d{1,2}N\d{1,2}', text)) > 0)) # positive
                      and ('sốt xuất huyết' not in text) # mistaken articles
                      and (('vắc xin' not in text) and ('tiêm phòng' not in text) and ('tiêm chủng' not in text))
                      for text in articles['Content']]
    init_filtered_data = articles.loc[initial_filter]

    # picking sentences that most likely contain information from article, gets context (+/- around main sentence)
    outbreak_data = []
    for idx, row in init_filtered_data.iterrows():
        # go through each article
        text = row['Content']
        key_sentences = []
        context = []
        sentences = text.split('.')
        for i, sentence in enumerate(sentences):
            # see which sentences might have information using keywords
            if (('bùng phát' in sentence) or ('dịch' in sentence)) and (any([lk in sentence for lk in location_keywords])):
                key_sentences.append(sentence.strip())
                context = [s.strip() for s in sentences[i-1:i+2]]
        if len(key_sentences) > 0:
            outbreak_data.append( (row['Date'], '. '.join(key_sentences), context) )
    outbreak_data = pd.DataFrame(outbreak_data, columns=['time', 'key_sentences', 'context'])

    # get locations of outbreaks from sentences by mention
    outbreak_locations = []
    for i, row in outbreak_data.iterrows():
        ks = row['key_sentences']
        loc = [l for l in locations if l in ks]
        if len(loc) == 0:
            loc = [l for l in locations if l in ('; '.join(row['context']))]
        print(ks, '\n', loc, '\n')
        outbreak_locations.append(loc)
    outbreak_data['location'] = outbreak_locations

    # output outbreak info
    with open('data/{}_outbreak_data.txt'.format(news_source), 'w') as f:
        for i, row in outbreak_data[['time', 'location']].iterrows():
            t, loc = row.values
            if len(loc) > 0:
                f.write('{}, {}\n'.format(t.date(), ';'.join(loc)))

if __name__ == '__main__':
    news_source = sys.argv[1]
    main(news_source)

