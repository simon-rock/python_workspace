#sentence = raw_input("Sentence: ")
sentence = "hello hello"
Screen_width = 80
text_width = len(sentence)
box_width = text_width + 6
left_margin = (Screen_width - box_width) // 2

print
print ' ' * left_margin + '+' + '-' * (box_width-4) + '+'
print ' ' * left_margin + '| '+ ' ' * text_width    +' |'
print ' ' * left_margin + '| '+  sentence           +' |'
print ' ' * left_margin + '| '+ ' ' * text_width    +' |'
print ' ' * left_margin + '+' + '-' * (box_width-4) + '+'
#print ' ' * left_margin + '+ '+ '-' * (box_width-4) + '+'
print '火车' #火车