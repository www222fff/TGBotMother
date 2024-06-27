# TGBotMother
auto create bot for account

# create bot
python auto_create_bot.py create 

Or with options as below:

python auto_create_bot.py create --interval 3 --proxy 135.245.192.7:8000

Prerequisite: Put photo file under photos dir

Note:
1) firstly execution need login code verification for session create, then later running will reuse session need not input verification code again.
   
   Begin verification for 8618560000000:
   
   Please enter the code you received: 92549 (input the code received in TG)

   Begin verification for 8618560000001:
   
   ...

3) create bot interval default as 60s to avoid too many attempts warning, you can try other value.

4) can only support change bot photo/name/about info.
   
5) Currently can auto generate 5 bots for each account, need to wait 24h for create more.

# delete all bots
python auto_create_bot.py delete

