from loop_watch import inspect
read={'tool':'fixture_read','arguments':{},'result':{'status':'waiting'}}
check={'tool':'fixture_check','arguments':{},'result':None}
signal=inspect([read,check]*3)
assert signal['review_required'] and signal['period']==2
print('REVIEW: two-record suffix repeated three times')
changed=dict(read,result={'status':'complete'})
assert not inspect([read,check]*3+[changed])['review_required']
print('NO SIGNAL: final result changed')
print('Synthetic records only. No tool called, stopped or retried.')
