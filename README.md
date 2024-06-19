# TGBotMother
auto create bot for account

# create bot
python auto_create_bot.py create --interval 60

Note:
1) firstly execution need login code verification for session create, then later running will reuse session need not input verification code again.
   
   Begin verification for 8618560000000:
   
   Please enter the code you received: 92458

3) create bot interval default as 60s to avoid too many attempts warning, you can try other value.

4) can only support change bot photo/name/about info.

# delete all bots
python auto_create_bot.py delete
