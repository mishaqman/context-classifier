# import nltk


# category = {1:['Adam','John'], 2:['Rohit', 'Dube']}

# token_to_category = {}
# for c in category.keys():
# 	for t in category[c]:
# 		if t not in token_to_category.keys():
# 			token_to_category[t] = []
# 		token_to_category[t].append(c)

# sentence = 'Rohit works in finance.'

# tokens = nltk.word_tokenize(sentence)

# print(tokens)

# for t in tokens:
# 	if t in token_to_category.keys():
# 		print([t,token_to_category[t]])

data = {'hey' :2, 'dey' :5}
summ = sum(data.values())
data = {k:(v/summ) for k,v in data.items()}
data = sorted (data.items(), key = lambda x:x[1], reverse = True)
import utils
v = 0.09876438676
digits = 4
v = int(float(v*10**digits))/10**digits
print(v)