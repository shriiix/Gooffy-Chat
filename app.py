from flask import Flask, render_template, request
from flask_socketio import SocketIO
import random
import time
import threading
import json
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store for active users and chat messages
active_users = set()
chat_messages = []
user_states = {}  # Track conversation state with each user

# Product information with enhanced details
products = [
    {
        "id": "ultraphone-x",
        "name": "UltraPhone X",
        "tagline": "The future of communication in your hands",
        "description": "The UltraPhone X is our most advanced smartphone ever, featuring groundbreaking technology that's changing how people connect with the world.",
        "features": ["8K OLED display", "48-hour battery life", "Quantum AI processor", "Holographic projector", "1TB storage"],
        "price": "$999",
        "pros": ["Revolutionary camera system with 108MP main sensor", "Fastest processor on the market - 50% faster than competitors", "Advanced AI assistant that learns your habits", "Waterproof up to 10 meters"],
        "cons": ["Premium price point", "Learning curve for new features"],
        "rating": 4.8,
        "image": "ultraphone-x.jpg",
        "release_date": "2023-10-15",
        "colors": ["Cosmic Black", "Arctic Silver", "Sunset Gold"]
    },
    {
        "id": "cloudbook-pro",
        "name": "CloudBook Pro",
        "tagline": "Power and elegance in perfect harmony",
        "description": "The CloudBook Pro redefines what a laptop can do, combining incredible performance with all-day battery life in a stunning design.",
        "features": ["16-inch Retina XDR display", "32GB unified memory", "1TB SSD", "Neural engine processor", "Studio-quality microphones"],
        "price": "$1499",
        "pros": ["Incredible performance for creative professionals", "Beautiful color-accurate display", "18-hour battery life", "Silent fanless design"],
        "cons": ["Limited ports (USB-C only)", "Not ideal for high-end gaming"],
        "rating": 4.7,
        "image": "cloudbook-pro.jpg",
        "release_date": "2023-09-01",
        "colors": ["Space Gray", "Silver", "Midnight Blue"]
    },
    {
        "id": "fittrack-ultra",
        "name": "FitTrack Ultra",
        "tagline": "Your personal health revolution",
        "description": "The FitTrack Ultra isn't just a fitness tracker - it's your personal health companion that provides insights you can actually use.",
        "features": ["Advanced heart rate monitoring", "Sleep analysis with REM detection", "Automatic workout detection", "7-day battery life", "ECG and blood oxygen sensors"],
        "price": "$199",
        "pros": ["Most accurate fitness metrics in its class", "Comfortable for 24/7 wear", "Intuitive companion app with coaching", "Water resistant to 50m"],
        "cons": ["No built-in GPS (uses phone)", "Limited smartwatch features compared to premium models"],
        "rating": 4.6,
        "image": "fittrack-ultra.jpg",
        "release_date": "2023-08-10",
        "colors": ["Obsidian Black", "Coral Pink", "Ocean Blue"]
    },
    {
        "id": "soundpods-pro",
        "name": "SoundPods Pro",
        "tagline": "Immersive sound, unmatched clarity",
        "description": "SoundPods Pro deliver an audio experience that puts you in the center of your music with intelligent noise cancellation and spatial audio.",
        "features": ["Active noise cancellation", "Spatial audio with head tracking", "10-hour battery life", "Voice assistant integration", "Transparency mode"],
        "price": "$249",
        "pros": ["Studio-quality sound profile", "Best-in-class noise cancellation", "Seamless device switching", "Comfortable for extended wear"],
        "cons": ["Premium pricing", "Case is slightly bulkier than competitors"],
        "rating": 4.7,
        "image": "soundpods-pro.jpg",
        "release_date": "2023-07-20",
        "colors": ["Matte Black", "Pearl White", "Forest Green"]
    }
]

# Bot personas with enhanced personalities and quirks
bot_personas = [
    {
        "name": "TechGuru",
        "emoji": "🤓",
        "personality": "enthusiastic and knowledgeable",
        "style": "Uses technical jargon and is always excited about new features",
        "role": "Product expert who knows all specifications",
        "quirks": ["Always mentions specs", "Gets overly excited about minor features", "Corrects others on technical details"],
        "favorite_product": "UltraPhone X",
        "catchphrases": ["Actually, technically speaking...", "The specs are mind-blowing!", "Let me break it down for you..."],
        "greetings": ["Hey tech enthusiast!", "What's up, gadget lover?", "Hello there, fellow tech fan!"],
        "casual_questions": ["What gadgets are you using these days?", "Have you tried any cool tech recently?", "What's your favorite piece of tech?"]
    },
    {
        "name": "BudgetSavvy",
        "emoji": "💰",
        "personality": "practical and value-conscious",
        "style": "Always compares prices and focuses on value for money",
        "role": "Helps users find the best deals and alternatives",
        "quirks": ["Always mentions the price", "Skeptical of premium features", "Suggests waiting for sales"],
        "favorite_product": "FitTrack Ultra",
        "catchphrases": ["But is it worth the price?", "You could save money by...", "Let's talk about value proposition..."],
        "greetings": ["Hey there, smart shopper!", "What's up, savvy consumer?", "Hello friend! Looking for good deals today?"],
        "casual_questions": ["Found any good deals lately?", "What was your last big purchase?", "Are you saving up for anything special?"]
    },
    {
        "name": "LifestyleCoach",
        "emoji": "✨",
        "personality": "trendy and lifestyle-focused",
        "style": "Relates products to lifestyle improvements and trends",
        "role": "Explains how products fit into modern lifestyles",
        "quirks": ["Uses slang", "Mentions celebrities who use products", "Talks about Instagram-worthy features"],
        "favorite_product": "SoundPods Pro",
        "catchphrases": ["This is totally going to elevate your vibe!", "It's not just a product, it's a lifestyle!", "Everyone's obsessed with this right now!"],
        "greetings": ["Hey there, beautiful people!", "What's the vibe today?", "Hey bestie! How's life treating you?"],
        "casual_questions": ["What's your aesthetic these days?", "How's your day going?", "Any exciting plans for the weekend?"]
    },
    {
        "name": "HonestReviewer",
        "emoji": "🔍",
        "personality": "straightforward and balanced",
        "style": "Gives balanced opinions, mentioning both pros and cons",
        "role": "Provides honest assessments of products",
        "quirks": ["Always mentions a downside", "Compares to competitors", "References user reviews"],
        "favorite_product": "CloudBook Pro",
        "catchphrases": ["Let's be honest here...", "The reviews are mixed on that feature...", "I have to point out that..."],
        "greetings": ["Hey there! Good to see you.", "Hello! How's everything going?", "Hi friend! What brings you here today?"],
        "casual_questions": ["What products have you been using lately?", "Had any good or bad experiences with tech recently?", "What features matter most to you in products?"]
    },
    {
        "name": "TechSkeptic",
        "emoji": "🙄",
        "personality": "cynical and hard to impress",
        "style": "Questions the value of new technology and points out flaws",
        "role": "Plays devil's advocate and challenges marketing claims",
        "quirks": ["Rolls eyes at new features", "Brings up past product failures", "Doubts marketing claims"],
        "favorite_product": "None - skeptical of all",
        "catchphrases": ["Yeah, right...", "We've heard that before!", "I'll believe it when I see it."],
        "greetings": ["Oh, another person buying into the hype...", "Hey there. Don't believe everything they tell you.", "Well hello... looking for the next overpriced gadget?"],
        "casual_questions": ["Why do you even need new tech?", "Ever think about how quickly these things become obsolete?", "Do you actually use all the features you pay for?"]
    }
]

# Casual conversation patterns and responses
casual_conversation_patterns = [
    # Greetings
    {
        "patterns": [
            r"(?:hi|hello|hey|howdy|sup|greetings)(?:\s|$)",
            r"(?:good\s)?(?:morning|afternoon|evening|day)(?:\s|$)",
            r"^yo(?:\s|$)",
        ],
        "responses": [
            "{bot_name} {emoji}: Hey {username}! How's it going today?",
            "{bot_name} {emoji}: {greeting} What brings you to our chat?",
            "{bot_name} {emoji}: Hello there, {username}! Nice to see you. {casual_question}",
            "{bot_name} {emoji}: Hey buddy! How's your day been so far?",
            "{bot_name} {emoji}: What's up {username}! Good to have you here."
        ]
    },
    # How are you / How's it going
    {
        "patterns": [
            r"(?:how are|how're) you",
            r"how(?:'s| is) it going",
            r"what'?s up",
            r"how(?:'s| is) (?:your|the) day",
            r"how(?:'s| is) life",
        ],
        "responses": [
            "{bot_name} {emoji}: I'm doing great, thanks for asking! {casual_question}",
            "{bot_name} {emoji}: Pretty good! Been helping people find the perfect tech all day. How about you?",
            "{bot_name} {emoji}: Can't complain! {catchphrase} {casual_question}",
            "{bot_name} {emoji}: All good here in the digital world! Have you been checking out any of our products?",
            "{bot_name} {emoji}: Fantastic! Just excited to chat about the latest tech. {casual_question}"
        ]
    },
    # Thank you / Thanks
    {
        "patterns": [
            r"thank(?:s| you)",
            r"appreciate (?:it|that)",
            r"that(?:'s| is) helpful",
            r"(?:great|good) (?:info|information)",
        ],
        "responses": [
            "{bot_name} {emoji}: You're most welcome, {username}! Happy to help.",
            "{bot_name} {emoji}: Anytime! That's what I'm here for. Anything else you'd like to know?",
            "{bot_name} {emoji}: No problem at all! {casual_question}",
            "{bot_name} {emoji}: Glad I could help! Let me know if you have any other questions.",
            "{bot_name} {emoji}: My pleasure! {catchphrase} Is there anything else you're curious about?"
        ]
    },
    # Doing well responses
    {
        "patterns": [
            r"(?:i'?m |i am )(?:good|great|fine|okay|not bad)",
            r"(?:doing|going) (?:good|great|fine|well|okay)",
            r"all good",
            r"pretty good",
        ],
        "responses": [
            "{bot_name} {emoji}: That's great to hear! {casual_question}",
            "{bot_name} {emoji}: Awesome! {catchphrase} Speaking of good things, have you checked out our {random_product}?",
            "{bot_name} {emoji}: Glad to hear it! Anything specific you're looking for today?",
            "{bot_name} {emoji}: Nice! I'm curious - {casual_question}",
            "{bot_name} {emoji}: Good to hear! You know what else is good? Our new {random_product}! Just saying... 😉"
        ]
    },
    # Not doing well responses
    {
        "patterns": [
            r"(?:i'?m |i am )(?:not |feeling )?(?:bad|sad|tired|exhausted|sick|unwell)",
            r"(?:been |having )?(?:a )?(?:bad|rough|tough) (?:day|time|week)",
            r"could be better",
            r"not (?:so|that) (?:good|great|well)",
        ],
        "responses": [
            "{bot_name} {emoji}: Sorry to hear that. Hope your day gets better! Maybe checking out some cool tech will cheer you up?",
            "{bot_name} {emoji}: Aw, that's too bad. Sometimes a new gadget can brighten the mood! Anything I can help with?",
            "{bot_name} {emoji}: Hang in there! {catchphrase} What brings you to our chat today?",
            "{bot_name} {emoji}: We all have those days! Want to take your mind off things and talk about some awesome products?",
            "{bot_name} {emoji}: Hope things improve soon! Maybe I can help you find something nice for yourself?"
        ]
    },
    # Recent purchases
    {
        "patterns": [
            r"(?:i|we) (?:just |recently )?(?:bought|purchased|got|acquired)",
            r"(?:i|we) (?:have|own|use)",
            r"my (?:new|recent) (?:purchase|buy|acquisition)",
        ],
        "responses": [
            "{bot_name} {emoji}: Oh nice! How are you liking it so far? {catchphrase}",
            "{bot_name} {emoji}: That's awesome! Have you tried all the features yet?",
            "{bot_name} {emoji}: Cool choice! You know, you might also like our {random_product} as a complement to that.",
            "{bot_name} {emoji}: Great pick! What made you choose that particular one?",
            "{bot_name} {emoji}: Nice! {catchphrase} Would you recommend it to others?"
        ]
    },
    # Looking for recommendations
    {
        "patterns": [
            r"(?:what|which) (?:should|would) (?:i|you) (?:recommend|suggest)",
            r"(?:looking for|need) (?:a |some )?(?:recommendation|suggestion)",
            r"(?:can|could) you (?:recommend|suggest)",
            r"what(?:'s| is) (?:good|best|better)",
        ],
        "responses": [
            "{bot_name} {emoji}: I'd be happy to help! What kind of product are you looking for specifically?",
            "{bot_name} {emoji}: {catchphrase} It depends on your needs! Are you looking for a phone, laptop, fitness tracker, or audio device?",
            "{bot_name} {emoji}: I personally love the {random_product}! It's been really popular lately. What's your budget range?",
            "{bot_name} {emoji}: The {random_product} is amazing if you're looking for {random_feature}. What features matter most to you?",
            "{bot_name} {emoji}: Let me help you find the perfect match! What will you be using it for mostly?"
        ]
    }
]

# Product-related questions and response templates
product_qa_templates = [
    # General product questions
    {
        "patterns": [
            r"what(?:'s| is) (?:the )?(?P<product>[\w\s-]+)(?:\?)?",
            r"tell me about (?:the )?(?P<product>[\w\s-]+)(?:\?)?",
            r"info on (?:the )?(?P<product>[\w\s-]+)(?:\?)?",
        ],
        "responses": [
            "{bot_name} {emoji}: The {product_name} is {tagline}! {description} It's priced at {price} and comes in {colors}.",
            "{bot_name} {emoji}: Oh, the {product_name}! It's {tagline}. {description} Released on {release_date}, it's been making waves in the market!",
            "{bot_name} {emoji}: {product_name} is one of our most popular products! {description} At {price}, it offers incredible value."
        ]
    },
    # Feature questions
    {
        "patterns": [
            r"what (?:are|'re) (?:the )?features of (?:the )?(?P<product>[\w\s-]+)(?:\?)?",
            r"what (?:can|does) (?:the )?(?P<product>[\w\s-]+) do(?:\?)?",
            r"(?P<product>[\w\s-]+) features(?:\?)?",
            r"(?P<product>[\w\s-]+) specs(?:\?)?",
        ],
        "responses": [
            "{bot_name} {emoji}: The {product_name} comes with: {features_list}. Pretty impressive, right?",
            "{bot_name} {emoji}: {product_name} is packed with features! It has {features_list}. My personal favorite is the {random_feature}!",
            "{bot_name} {emoji}: Let me tell you about the {product_name}! It features {features_list}. At {price}, you're getting cutting-edge technology."
        ]
    },
    # Price questions
    {
        "patterns": [
            r"how much (?:is|does) (?:the )?(?P<product>[\w\s-]+) cost(?:\?)?",
            r"(?P<product>[\w\s-]+) price(?:\?)?",
            r"what(?:'s| is) the price of (?:the )?(?P<product>[\w\s-]+)(?:\?)?",
        ],
        "responses": [
            "{bot_name} {emoji}: The {product_name} is priced at {price}. Considering its {random_feature}, I'd say it's a great value!",
            "{bot_name} {emoji}: You can get the {product_name} for {price}. It's an investment in quality - especially with the {random_feature}.",
            "{bot_name} {emoji}: The {product_name} costs {price}. Compare that to competitors and you'll see why it's flying off the shelves!"
        ]
    },
    # Comparison questions
    {
        "patterns": [
            r"(?:how|is) (?:the )?(?P<product>[\w\s-]+) compared to",
            r"(?P<product>[\w\s-]+) vs",
            r"(?P<product>[\w\s-]+) or",
        ],
        "responses": [
            "{bot_name} {emoji}: The {product_name} stands out with its {random_feature}. While competitors might offer similar products, our {rating}/5 rating speaks for itself!",
            "{bot_name} {emoji}: What makes the {product_name} special is {random_pro}. That's why customers rate it {rating}/5!",
            "{bot_name} {emoji}: Compared to alternatives, the {product_name} excels in {random_feature} and {random_pro}. It's why we have a {rating}/5 rating!"
        ]
    },
    # Opinion questions
    {
        "patterns": [
            r"(?:is|are) (?:the )?(?P<product>[\w\s-]+) good(?:\?)?",
            r"(?:do you|would you) recommend (?:the )?(?P<product>[\w\s-]+)(?:\?)?",
            r"(?:should|worth) (?:i|it) (?:get|buy|purchase) (?:the )?(?P<product>[\w\s-]+)(?:\?)?",
        ],
        "responses": [
            "{bot_name} {emoji}: The {product_name} is fantastic! With a {rating}/5 rating, customers love the {random_feature}. Though {random_con}, the {random_pro} more than makes up for it.",
            "{bot_name} {emoji}: I highly recommend the {product_name}! The {random_feature} is game-changing, and {random_pro}. Just be aware that {random_con}.",
            "{bot_name} {emoji}: Is the {product_name} worth it? The {random_feature} and {random_pro} make it a great choice. Some mention {random_con}, but most users don't find it to be a deal-breaker."
        ]
    },
    # General inquiry
    {
        "patterns": [
            r"(?:what|which) products do you (?:have|offer|sell)(?:\?)?",
            r"(?:show|tell) me (?:your|the) products(?:\?)?",
            r"what(?:'s| is) (?:new|popular|trending)(?:\?)?",
        ],
        "responses": [
            "{bot_name} {emoji}: We have several amazing products! Our lineup includes the UltraPhone X, CloudBook Pro, FitTrack Ultra, and SoundPods Pro. Which one are you interested in?",
            "{bot_name} {emoji}: Our current product lineup is exciting! We have the UltraPhone X (smartphone), CloudBook Pro (laptop), FitTrack Ultra (fitness tracker), and SoundPods Pro (earbuds). Would you like details on any of these?",
            "{bot_name} {emoji}: We're currently featuring the UltraPhone X, CloudBook Pro, FitTrack Ultra, and SoundPods Pro - all cutting-edge products in their categories! What would you like to know about them?"
        ]
    }
]

# Enhanced bot conversation templates with personality and humor
bot_conversation_templates = [
    # Casual chat between bots
    {
        "topic": "casual_chat",
        "conversation": [
            "{bot1_name} {bot1_emoji}: Hey {bot2_name}, how's your day going?",
            "{bot2_name} {bot2_emoji}: Pretty good! Just helped someone pick out a new {product_name}. You?",
            "{bot1_name} {bot1_emoji}: {catchphrase1} Been comparing the {feature1} on different models. The {product_name} really stands out!",
            "{bot2_name} {bot2_emoji}: {catchphrase2} I know, right? Though I still think the {con1} could be improved.",
            "{bot3_name} {bot3_emoji}: Hey guys! What are we talking about?",
            "{bot1_name} {bot1_emoji}: Just chatting about the {product_name}. {bot3_name}, didn't you just try one out?",
            "{bot3_name} {bot3_emoji}: Yeah! The {feature2} blew me away. {catchphrase3} I've been recommending it to everyone!",
            "{bot2_name} {bot2_emoji}: You're such a fan! But I have to admit, the {feature3} is pretty impressive."
        ]
    },
    # Product debate
    {
        "topic": "product_debate",
        "conversation": [
            "{bot1_name} {bot1_emoji}: The {product_name} is absolutely revolutionary! The {feature1} is going to change everything about how we use {product_category}s!",
            "{bot2_name} {bot2_emoji}: {catchphrase2} Are you serious? It's just another overpriced {product_category}. You can get the same {feature1} on competitors for half the price.",
            "{bot1_name} {bot1_emoji}: {catchphrase1} The build quality alone justifies the price. Plus, the {feature2} is miles ahead of anything else on the market.",
            "{bot2_name} {bot2_emoji}: Sure, if you enjoy paying premium prices for features you'll never use. Most people don't even need {feature2}!",
            "{bot3_name} {bot3_emoji}: {catchphrase3} Both of you have points. The {product_name} is premium, but it does offer {feature3} which is genuinely useful for many people.",
            "{bot1_name} {bot1_emoji}: Exactly! And don't forget the {pro1}. That alone is worth the price.",
            "{bot2_name} {bot2_emoji}: But you have to admit the {con1} is a real drawback. My cousin bought one and keeps complaining about it.",
            "{bot3_name} {bot3_emoji}: Let's be real - it depends on what you need. If you value {feature1} and don't mind the {con1}, it's a great choice."
        ]
    },
    # Product teasing
    {
        "topic": "product_teasing",
        "conversation": [
            "{bot1_name} {bot1_emoji}: Just got my new {product_name} and I'm absolutely loving it! The {feature1} is incredible!",
            "{bot2_name} {bot2_emoji}: {catchphrase2} Oh please, you're such a fanboy/fangirl. I bet you haven't even tried the {feature1} yet.",
            "{bot1_name} {bot1_emoji}: Actually, I've been using it all day! The {feature2} is so intuitive, even YOU could figure it out.",
            "{bot2_name} {bot2_emoji}: Very funny. I just think it's hilarious how excited people get over a slightly improved {product_category}.",
            "{bot1_name} {bot1_emoji}: {catchphrase1} It's not slight! The {pro1} is a game-changer. But I wouldn't expect someone still using last year's tech to understand.",
            "{bot3_name} {bot3_emoji}: {catchphrase3} Come on, both of you! The {product_name} is good, but let's not act like it's life-changing. Though I do love the {feature3}.",
            "{bot2_name} {bot2_emoji}: Fine, I admit the {feature3} is pretty cool. But is it worth {price}? I think not.",
            "{bot1_name} {bot1_emoji}: For something you use every day? Absolutely worth it. But hey, enjoy your outdated {product_category}!"
        ]
    },
    # Weekend plans
    {
        "topic": "weekend_plans",
        "conversation": [
            "{bot1_name} {bot1_emoji}: Anyone have exciting weekend plans? I'm thinking of testing the {product_name}'s {feature1} on a hike!",
            "{bot2_name} {bot2_emoji}: {catchphrase2} A hike? You're going to risk your {price} {product_category} on a hike?",
            "{bot1_name} {bot1_emoji}: That's the beauty of it! The {pro1} makes it perfect for outdoor adventures.",
            "{bot3_name} {bot3_emoji}: I'm planning to binge-watch shows using my {alternative_product}. The {feature3} makes it perfect for marathons.",
            "{bot2_name} {bot2_emoji}: Now THAT sounds like a proper weekend! Though the {alternative_product}'s {con1} might get annoying after a few hours.",
            "{bot1_name} {bot1_emoji}: {catchphrase1} Both sound fun! The {product_name} would be great for either activity honestly.",
            "{bot3_name} {bot3_emoji}: {catchphrase3} Always bringing it back to your favorite product, aren't you {bot1_name}?",
            "{bot1_name} {bot1_emoji}: What can I say? When something's this good, it's hard not to talk about it!"
        ]
    },
    # Product support
    {
        "topic": "product_support",
        "conversation": [
            "{bot1_name} {bot1_emoji}: Is anyone else having issues with the {feature1} on their {product_name}? Mine keeps glitching.",
            "{bot2_name} {bot2_emoji}: Have you tried turning it off and on again? Works every time for me!",
            "{bot1_name} {bot1_emoji}: {catchphrase1} Very funny. Yes, I've tried that AND reset to factory settings.",
            "{bot3_name} {bot3_emoji}: {catchphrase3} There was actually a software update yesterday that fixes that exact issue with the {feature1}.",
            "{bot1_name} {bot1_emoji}: Really? Let me check... You're right! Updating now.",
            "{bot2_name} {bot2_emoji}: {catchphrase2} This is why I always wait a month before buying new tech. Let other people deal with the bugs!",
            "{bot3_name} {bot3_emoji}: The {product_name} has actually been really stable compared to previous models. This is the first major bug.",
            "{bot1_name} {bot1_emoji}: Update complete and it's working perfectly now! The {feature1} is actually amazing when it works properly."
        ]
    },
    {
        "topic": "tech_trends",
        "conversation": [
            "{bot1_name} {bot1_emoji}: Did you all see that article about the future of {product_category} technology? They're saying {feature1} will be standard in all devices next year.",
            "{bot2_name} {bot2_emoji}: {catchphrase2} That's just marketing hype. They've been promising advanced {feature1} for years now.",
            "{bot1_name} {bot1_emoji}: Not this time! The {product_name} already has it, and it works amazingly well.",
            "{bot3_name} {bot3_emoji}: I've actually tested the {feature1} on the {product_name}, and I have to say, it's impressive. {catchphrase3}",
            "{bot2_name} {bot2_emoji}: Well, I'll believe it when I see widespread adoption. Most people don't even use half the features on their devices.",
            "{bot1_name} {bot1_emoji}: {catchphrase1} That's because most features aren't as game-changing as this one. The {feature1} on the {product_name} actually saves me hours every week.",
            "{bot3_name} {bot3_emoji}: I think once people experience it, they won't go back. It's like when touchscreens first became mainstream.",
            "{bot2_name} {bot2_emoji}: Fine, you've convinced me to at least try it. But I'm still skeptical about the {price} price tag just for {feature1}."
        ]
    },
    {
        "topic": "customer_experience",
        "conversation": [
            "{bot1_name} {bot1_emoji}: Just helped a customer who was deciding between the {product_name} and the {alternative_product}. They were so confused!",
            "{bot2_name} {bot2_emoji}: {catchphrase2} What did they end up choosing?",
            "{bot1_name} {bot1_emoji}: The {product_name}, of course! Once I showed them the {feature1}, they were sold.",
            "{bot3_name} {bot3_emoji}: That {feature1} is impressive, but did you mention the {con1}? {catchphrase3} We should be transparent.",
            "{bot1_name} {bot1_emoji}: Of course I did! {catchphrase1} But they said the {pro1} was more important for their needs.",
            "{bot2_name} {bot2_emoji}: That makes sense. Different users have different priorities. I always ask about their use case first.",
            "{bot3_name} {bot3_emoji}: Exactly! For someone who values {feature2}, the {product_name} is perfect. But if they care more about price...",
            "{bot1_name} {bot1_emoji}: Then the {alternative_product} might be better. It's all about matching the right product to the right person!"
        ]
    },
    {
        "topic": "product_rumors",
        "conversation": [
            "{bot1_name} {bot1_emoji}: Have you heard the rumors about the next version of the {product_name}? They're saying it will have {feature1} that's twice as powerful!",
            "{bot2_name} {bot2_emoji}: {catchphrase2} Those rumors come out every year, and they're always exaggerated.",
            "{bot3_name} {bot3_emoji}: I don't know, my sources are pretty reliable. They also mentioned improved {feature2} and fixing the {con1} issue.",
            "{bot1_name} {bot1_emoji}: {catchphrase1} If they fix the {con1}, it would be perfect! The current {product_name} is already amazing.",
            "{bot2_name} {bot2_emoji}: Even if they do, they'll probably increase the price from {price} to something even more ridiculous.",
            "{bot3_name} {bot3_emoji}: {catchphrase3} Price increases are inevitable with new technology. But early adopters always pay premium.",
            "{bot1_name} {bot1_emoji}: True, but for cutting-edge {feature1} and {feature2}, many people would gladly pay extra.",
            "{bot2_name} {bot2_emoji}: We'll see. I still recommend waiting for reviews before pre-ordering anything, no matter how exciting it sounds."
        ]
    }
]

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def handle_join(data):
    username = data.get('username')
    if username:
        active_users.add(username)
        # Initialize user state
        user_states[username] = {
            "last_interaction": time.time(),
            "conversation_stage": "greeting",
            "asked_personal_question": False,
            "mentioned_products": set()
        }
        
        # Send chat history to new user
        for message in chat_messages[-50:]:  # Send last 50 messages
            socketio.emit('message', message, to=request.sid)
        # Notify everyone about new user
        socketio.emit('user_joined', {'username': username, 'active_users': list(active_users)})
        
        # Welcome message with casual greeting
        bot = random.choice(bot_personas)
        greeting = random.choice(bot['greetings'])
        casual_question = random.choice(bot['casual_questions'])
        
        welcome_message = {
            'username': f"{bot['name']} {bot['emoji']}",
            'message': f"{greeting} Welcome to our chat, {username}! {casual_question}",
            'timestamp': time.strftime('%H:%M:%S'),
            'is_bot': True
        }
        chat_messages.append(welcome_message)
        socketio.emit('message', welcome_message)
        
        # Have another bot chime in after a short delay
        def send_second_welcome():
            time.sleep(random.uniform(2, 4))
            second_bot = random.choice([b for b in bot_personas if b['name'] != bot['name']])
            
            second_welcome = {
                'username': f"{second_bot['name']} {second_bot['emoji']}",
                'message': f"Hey {username}! Great to have you join us. We were just chatting about the latest tech. Anything specific you're interested in?",
                'timestamp': time.strftime('%H:%M:%S'),
                'is_bot': True
            }
            chat_messages.append(second_welcome)
            socketio.emit('message', second_welcome)
            
            # After a bit, introduce a product showcase
            time.sleep(random.uniform(3, 5))
            product = random.choice(products)
            showcase_message = {
                'username': f"{bot['name']} {bot['emoji']}",
                'message': f"By the way, have you seen our featured product today? The {product['name']} - {product['tagline']}! It's been really popular.",
                'timestamp': time.strftime('%H:%M:%S'),
                'is_bot': True,
                'product_card': {
                    'id': product['id'],
                    'name': product['name'],
                    'description': product['description'],
                    'price': product['price'],
                    'rating': product['rating'],
                    'image': product['image']
                }
            }
            chat_messages.append(showcase_message)
            socketio.emit('message', showcase_message)
        
        welcome_thread = threading.Thread(target=send_second_welcome)
        welcome_thread.daemon = True
        welcome_thread.start()

@socketio.on('message')
def handle_message(data):
    username = data.get('username')
    message_text = data.get('message')
    
    if username and message_text:
        # Add user message to chat
        message = {
            'username': username,
            'message': message_text,
            'timestamp': time.strftime('%H:%M:%S')
        }
        chat_messages.append(message)
        socketio.emit('message', message)
        
        # Update user state
        if username in user_states:
            user_states[username]["last_interaction"] = time.time()
        
        # Process message to see if it matches casual patterns or product questions
        threading.Thread(target=process_user_message, args=(message_text, username)).start()
        
        # Set up a fallback response in case no bot responds directly
        trigger_bot_response_to_user(username)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def find_product_by_name_fuzzy(product_name):
    """Find a product by name with fuzzy matching"""
    product_name = product_name.lower()
    
    # Direct match first
    for product in products:
        if product_name == product['name'].lower() or product_name == product['id'].lower():
            return product
    
    # Partial match
    for product in products:
        if product_name in product['name'].lower() or product['name'].lower() in product_name:
            return product
    
    # Check for common product types
    product_types = {
        'phone': 'UltraPhone X',
        'smartphone': 'UltraPhone X',
        'laptop': 'CloudBook Pro',
        'computer': 'CloudBook Pro',
        'notebook': 'CloudBook Pro',
        'fitness': 'FitTrack Ultra',
        'tracker': 'FitTrack Ultra',
        'watch': 'FitTrack Ultra',
        'earbuds': 'SoundPods Pro',
        'headphones': 'SoundPods Pro',
        'earphones': 'SoundPods Pro',
        'pods': 'SoundPods Pro',
        'audio': 'SoundPods Pro'
    }
    
    for keyword, product_name in product_types.items():
        if keyword in product_name.lower():
            for product in products:
                if product['name'] == product_name:
                    return product
    
    return None

def extract_context_from_message(message_text):
    """Extract context and keywords from user messages for better responses"""
    context = {
        "keywords": [],
        "sentiment": "neutral",
        "question_type": None,
        "mentioned_products": []
    }
    
    # Extract keywords
    common_keywords = ["price", "features", "compare", "better", "worth", "buy", "recommend", 
                      "quality", "battery", "screen", "camera", "performance", "review", 
                      "problem", "issue", "alternative", "versus", "vs", "difference"]
    
    for keyword in common_keywords:
        if keyword in message_text.lower():
            context["keywords"].append(keyword)
    
    # Detect sentiment
    positive_words = ["good", "great", "awesome", "excellent", "amazing", "love", "best", "perfect"]
    negative_words = ["bad", "terrible", "awful", "worst", "hate", "dislike", "poor", "expensive"]
    
    pos_count = sum(1 for word in positive_words if word in message_text.lower())
    neg_count = sum(1 for word in negative_words if word in message_text.lower())
    
    if pos_count > neg_count:
        context["sentiment"] = "positive"
    elif neg_count > pos_count:
        context["sentiment"] = "negative"
    
    # Detect question type
    if "?" in message_text:
        context["question_type"] = "direct_question"
    elif any(word in message_text.lower() for word in ["what", "how", "why", "when", "where", "which", "who"]):
        context["question_type"] = "implied_question"
    
    # Extract mentioned products
    for product in products:
        if product["name"].lower() in message_text.lower() or product["id"].lower() in message_text.lower():
            context["mentioned_products"].append(product["name"])
    
    return context

def process_user_message(message_text, username):
    """Process user message and generate bot response if appropriate"""
    # Wait a moment to simulate typing
    time.sleep(1)
    
    # Send typing indicator
    socketio.emit('bot_typing', {'is_typing': True})
    
    # Extract context from the message
    context = extract_context_from_message(message_text)
    
    # Select a random bot to respond
    bot = random.choice(bot_personas)
    
    # First check for casual conversation patterns
    for pattern_group in casual_conversation_patterns:
        for pattern in pattern_group['patterns']:
            if re.search(pattern, message_text.lower()):
                # Format casual response
                response_template = random.choice(pattern_group['responses'])
                greeting = random.choice(bot['greetings'])
                casual_question = random.choice(bot['casual_questions'])
                catchphrase = random.choice(bot['catchphrases'])
                random_product = random.choice(products)['name']
                random_feature = random.choice(random_product['features'] if isinstance(random_product, dict) else ["feature"])
                
                response = response_template.format(
                    bot_name=bot['name'],
                    emoji=bot['emoji'],
                    username=username,
                    greeting=greeting,
                    casual_question=casual_question,
                    catchphrase=catchphrase,
                    random_product=random_product,
                    random_feature=random_feature
                )
                
                # Wait a bit to simulate typing
                time.sleep(random.uniform(1.5, 3))
                
                # Stop typing indicator
                socketio.emit('bot_typing', {'is_typing': False})
                
                # Send response
                bot_message = {
                    'username': f"{bot['name']} {bot['emoji']}",
                    'message': response,
                    'timestamp': time.strftime('%H:%M:%S'),
                    'is_bot': True
                }
                
                chat_messages.append(bot_message)
                socketio.emit('message', bot_message)
                
                # Chance for another bot to chime in with a casual response
                if random.random() < 0.4:  # 40% chance
                    time.sleep(random.uniform(2, 4))
                    socketio.emit('bot_typing', {'is_typing': True})
                    time.sleep(random.uniform(1.5, 3))
                    
                    # Pick a different bot
                    second_bot = random.choice([b for b in bot_personas if b['name'] != bot['name']])
                    
                    # Generate a casual follow-up
                    followup_templates = [
                        "I agree with {bot_name}! {casual_question}",
                        "{catchphrase} I was just about to say something similar. {casual_question}",
                        "Hey {username}, {bot_name} is right! Also, have you heard about our {random_product}?",
                        "Jumping in to say hi too, {username}! {casual_question}",
                        "Welcome to the conversation! I'm curious - {casual_question}"
                    ]
                    
                    followup_template = random.choice(followup_templates)
                    followup = followup_template.format(
                        bot_name=bot['name'],
                        username=username,
                        catchphrase=random.choice(second_bot['catchphrases']),
                        casual_question=random.choice(second_bot['casual_questions']),
                        random_product=random.choice(products)['name']
                    )
                    
                    socketio.emit('bot_typing', {'is_typing': False})
                    
                    followup_message = {
                        'username': f"{second_bot['name']} {second_bot['emoji']}",
                        'message': followup,
                        'timestamp': time.strftime('%H:%M:%S'),
                        'is_bot': True
                    }
                    
                    chat_messages.append(followup_message)
                    socketio.emit('message', followup_message)
                
                return
    
    # Then check for product question patterns
    for qa_template in product_qa_templates:
        for pattern in qa_template['patterns']:
            match = re.search(pattern, message_text.lower())
            if match:
                # If we found a product name in the question
                if 'product' in match.groupdict():
                    product_name = match.group('product')
                    product = find_product_by_name_fuzzy(product_name)
                    
                    if product:
                        # Wait a bit longer to simulate thinking/typing
                        time.sleep(random.uniform(1.5, 3))
                        
                        # Format response
                        response_template = random.choice(qa_template['responses'])
                        random_feature = random.choice(product['features'])
                        random_pro = random.choice(product['pros'])
                        random_con = random.choice(product['cons'])
                        colors = ", ".join(product['colors'])
                        features_list = ", ".join(product['features'])
                        
                        response = response_template.format(
                            bot_name=bot['name'],
                            emoji=bot['emoji'],
                            product_name=product['name'],
                            tagline=product['tagline'],
                            description=product['description'],
                            price=product['price'],
                            rating=product['rating'],
                            random_feature=random_feature,
                            random_pro=random_pro,
                            random_con=random_con,
                            colors=colors,
                            features_list=features_list,
                            release_date=product['release_date']
                        )
                        
                        # Stop typing indicator
                        socketio.emit('bot_typing', {'is_typing': False})
                        
                        # Send response with product card
                        bot_message = {
                            'username': f"{bot['name']} {bot['emoji']}",
                            'message': response,
                            'timestamp': time.strftime('%H:%M:%S'),
                            'is_bot': True,
                            'product_card': {
                                'id': product['id'],
                                'name': product['name'],
                                'description': product['description'],
                                'price': product['price'],
                                'rating': product['rating'],
                                'image': product['image']
                            }
                        }
                        
                        chat_messages.append(bot_message)
                        socketio.emit('message', bot_message)
                        
                        # Update user state to track mentioned products
                        if username in user_states:
                            user_states[username]["mentioned_products"].add(product['name'])
                        
                        # Chance for another bot to chime in with a different opinion
                        if random.random() < 0.7:  # 70% chance
                            time.sleep(random.uniform(2, 4))
                            socketio.emit('bot_typing', {'is_typing': True})
                            time.sleep(random.uniform(1.5, 3))
                            
                            # Pick a different bot
                            second_bot = random.choice([b for b in bot_personas if b['name'] != bot['name']])
                            
                            # Generate a response based on the second bot's personality
                            if second_bot['name'] == "TechSkeptic":
                                followup = f"{second_bot['name']} {second_bot['emoji']}: {random.choice(second_bot['catchphrases'])} The {product['name']} isn't as great as {bot['name']} makes it sound. Sure, the {random_feature} is decent, but {random_con} is a real issue. You could get better value elsewhere."
                            elif second_bot['name'] == "BudgetSavvy":
                                followup = f"{second_bot['name']} {second_bot['emoji']}: {random.choice(second_bot['catchphrases'])} At {product['price']}, you should really consider if you need all those features. The {random_feature} is nice, but is it worth the premium?"
                            elif product['name'] == second_bot['favorite_product']:
                                followup = f"{second_bot['name']} {second_bot['emoji']}: I actually agree with {bot['name']} for once! The {product['name']} is my favorite product. The {random_feature} is even better than described!"
                            else:
                                followup = f"{second_bot['name']} {second_bot['emoji']}: {random.choice(second_bot['catchphrases'])} I have a different take on the {product['name']}. While the {random_feature} is good, don't forget about {random_con}. Just something to consider!"
                            
                            socketio.emit('bot_typing', {'is_typing': False})
                            
                            followup_message = {
                                'username': f"{second_bot['name']} {second_bot['emoji']}",
                                'message': followup,
                                'timestamp': time.strftime('%H:%M:%S'),
                                'is_bot': True
                            }
                            
                            chat_messages.append(followup_message)
                            socketio.emit('message', followup_message)
                            
                            # Chance for user follow-up question suggestion
                            if random.random() < 0.5:  # 50% chance
                                time.sleep(random.uniform(2, 3))
                                
                                third_bot = random.choice([b for b in bot_personas if b['name'] != bot['name'] and b['name'] != second_bot['name']])
                                
                                followup_questions = [
                                    f"Hey {username}, did you want to know about any specific feature of the {product['name']}?",
                                    f"{username}, are you considering the {product['name']} for yourself or as a gift?",
                                    f"By the way {username}, what matters most to you in a {product['name']}? Battery life? Performance? Design?",
                                    f"Just curious {username}, what are you currently using before considering the {product['name']}?"
                                ]
                                
                                personal_followup = {
                                    'username': f"{third_bot['name']} {third_bot['emoji']}",
                                    'message': random.choice(followup_questions),
                                    'timestamp': time.strftime('%H:%M:%S'),
                                    'is_bot': True
                                }
                                
                                chat_messages.append(personal_followup)
                                socketio.emit('message', personal_followup)
                        
                        return
                else:
                    # General product inquiry without specific product
                    time.sleep(random.uniform(1.5, 2.5))
                    
                    # Format response
                    response_template = random.choice(qa_template['responses'])
                    response = response_template.format(
                        bot_name=bot['name'],
                        emoji=bot['emoji']
                    )
                    
                    # Stop typing indicator
                    socketio.emit('bot_typing', {'is_typing': False})
                    
                    # Send response
                    bot_message = {
                        'username': f"{bot['name']} {bot['emoji']}",
                        'message': response,
                        'timestamp': time.strftime('%H:%M:%S'),
                        'is_bot': True
                    }
                    
                    chat_messages.append(bot_message)
                    socketio.emit('message', bot_message)
                    return
    
    # If we have context but no pattern matched, use the context to generate a response
    if not any(re.search(pattern, message_text.lower()) for pattern_group in casual_conversation_patterns for pattern in pattern_group['patterns']) and \
       not any(re.search(pattern, message_text.lower()) for qa_template in product_qa_templates for pattern in qa_template['patterns']):
        
        # If the user mentioned specific products
        if context["mentioned_products"]:
            product_name = context["mentioned_products"][0]
            product = next((p for p in products if p['name'] == product_name), None)
            
            if product:
                # Generate a contextual response based on keywords and sentiment
                if "price" in context["keywords"]:
                    response = f"{bot['name']} {bot['emoji']}: The {product['name']} is priced at {product['price']}. "
                    if context["sentiment"] == "negative":
                        response += f"I understand it might seem expensive, but considering the {random.choice(product['features'])}, many customers find it worth the investment."
                    else:
                        response += f"It's a competitive price for what you get, especially the {random.choice(product['features'])}!"
                
                elif "features" in context["keywords"] or "specs" in context["keywords"]:
                    features = ", ".join(product['features'])
                    response = f"{bot['name']} {bot['emoji']}: The {product['name']} comes with {features}. My personal favorite is the {random.choice(product['features'])}!"
                
                elif any(word in context["keywords"] for word in ["compare", "better", "versus", "vs"]):
                    response = f"{bot['name']} {bot['emoji']}: The {product['name']} stands out because of its {random.choice(product['pros'])}. Compared to competitors, it really excels in {random.choice(product['features'])}."
                
                elif any(word in context["keywords"] for word in ["problem", "issue"]):
                    response = f"{bot['name']} {bot['emoji']}: I'm sorry to hear you're having an issue with the {product['name']}. The most common concern is {random.choice(product['cons'])}, but there's usually a simple fix. Could you tell me more about what's happening?"
                
                else:
                    # Generic product response
                    response = f"{bot['name']} {bot['emoji']}: The {product['name']} is one of our most popular products! It features {random.choice(product['features'])} and customers particularly love the {random.choice(product['pros'])}."
                
                # Wait a bit to simulate typing
                time.sleep(random.uniform(1.5, 3))
                
                # Stop typing indicator
                socketio.emit('bot_typing', {'is_typing': False})
                
                # Send response with product card
                bot_message = {
                    'username': f"{bot['name']} {bot['emoji']}",
                    'message': response,
                    'timestamp': time.strftime('%H:%M:%S'),
                    'is_bot': True,
                    'product_card': {
                        'id': product['id'],
                        'name': product['name'],
                        'description': product['description'],
                        'price': product['price'],
                        'rating': product['rating'],
                        'image': product['image']
                    }
                }
                
                chat_messages.append(bot_message)
                socketio.emit('message', bot_message)
                
                # Update user state to track mentioned products
                if username in user_states:
                    user_states[username]["mentioned_products"].add(product['name'])
                
                # Have another bot chime in with a different perspective
                time.sleep(random.uniform(2, 4))
                second_bot = random.choice([b for b in bot_personas if b['name'] != bot['name']])
                
                # Generate a response based on the second bot's personality
                if second_bot['name'] == "TechSkeptic":
                    followup = f"{second_bot['name']} {second_bot['emoji']}: {random.choice(second_bot['catchphrases'])} I have to jump in here. While {bot['name']} makes some good points about the {product['name']}, let's not forget about {random.choice(product['cons'])}. Just something to consider, {username}."
                elif second_bot['name'] == "BudgetSavvy":
                    followup = f"{second_bot['name']} {second_bot['emoji']}: {random.choice(second_bot['catchphrases'])} I'd add that at {product['price']}, you should make sure you'll use all those features. What's your budget range, {username}?"
                else:
                    followup = f"{second_bot['name']} {second_bot['emoji']}: {random.choice(second_bot['catchphrases'])} I agree with {bot['name']} about the {product['name']}. {username}, what specific features are most important to you?"
                
                followup_message = {
                    'username': f"{second_bot['name']} {second_bot['emoji']}",
                    'message': followup,
                    'timestamp': time.strftime('%H:%M:%S'),
                    'is_bot': True
                }
                
                chat_messages.append(followup_message)
                socketio.emit('message', followup_message)
                return
        
        # If no specific product was mentioned but we have keywords
        if context["keywords"]:
            if "recommend" in context["keywords"] or "suggestion" in context["keywords"]:
                product = random.choice(products)
                response = f"{bot['name']} {bot['emoji']}: Based on what you're saying, {username}, I think you might like the {product['name']}. It's known for its {random.choice(product['features'])} and {random.choice(product['pros'])}. Would you like to know more about it?"
            elif "price" in context["keywords"]:
                response = f"{bot['name']} {bot['emoji']}: Are you looking for something in a specific price range, {username}? Our products range from {products[2]['price']} for the {products[2]['name']} to {products[1]['price']} for the {products[1]['name']}."
            else:
                # Generic response based on keywords
                response = f"{bot['name']} {bot['emoji']}: I noticed you mentioned {', '.join(context['keywords'][:2])}. Is there a specific product you're interested in learning about?"
            
            # Wait a bit to simulate typing
            time.sleep(random.uniform(1.5, 2.5))
            
            # Stop typing indicator
            socketio.emit('bot_typing', {'is_typing': False})
            
            # Send response
            bot_message = {
                'username': f"{bot['name']} {bot['emoji']}",
                'message': response,
                'timestamp': time.strftime('%H:%M:%S'),
                'is_bot': True
            }
            
            chat_messages.append(bot_message)
            socketio.emit('message', bot_message)
            return

    # If no specific pattern was matched, respond with a friendly message
    friendly_responses = [
        f"{bot['name']} {bot['emoji']}: Hey {username}! {random.choice(bot['casual_questions'])}",
        f"{bot['name']} {bot['emoji']}: I noticed you're interested in our chat! Feel free to ask about the UltraPhone X, CloudBook Pro, FitTrack Ultra, or SoundPods Pro.",
        f"{bot['name']} {bot['emoji']}: {random.choice(bot['catchphrases'])} What brings you to our chat today, {username}?",
        f"{bot['name']} {bot['emoji']}: Hi {username}! I'd be happy to tell you about our products. Just ask about any specific one you're curious about!",
        f"{bot['name']} {bot['emoji']}: Thanks for your message! What kind of tech are you interested in today?"
    ]
    
    # Wait a bit to simulate typing
    time.sleep(random.uniform(1, 2))
    
    # Stop typing indicator
    socketio.emit('bot_typing', {'is_typing': False})
    
    # Send generic response
    bot_message = {
        'username': f"{bot['name']} {bot['emoji']}",
        'message': random.choice(friendly_responses),
        'timestamp': time.strftime('%H:%M:%S'),
        'is_bot': True
    }
    
    chat_messages.append(bot_message)
    socketio.emit('message', bot_message)

def generate_bot_conversation():
    """Generate occasional conversations between bots about products with personality"""
    while True:
        # Wait between conversations - reduced wait time for more frequent interactions
        time.sleep(random.randint(25, 60))  # More frequent bot conversations
        
        # Select random product
        product = random.choice(products)
        
        # Select random conversation template
        template = random.choice(bot_conversation_templates)
        
        # Select random bot personas (ensure they're different)
        selected_bots = random.sample(bot_personas, 3)
        bot1, bot2, bot3 = selected_bots
        
        # Get product category
        product_categories = {
            'UltraPhone X': 'smartphone',
            'CloudBook Pro': 'laptop',
            'FitTrack Ultra': 'fitness tracker',
            'SoundPods Pro': 'earbud'
        }
        product_category = product_categories.get(product['name'], 'device')
        
        # Get alternative product and color
        all_products = [p for p in products if p['name'] != product['name']]
        alternative_product = random.choice(all_products)['name'] if all_products else "competitor product"
        alternative_color = random.choice(product['colors'])
        color = random.choice([c for c in product['colors'] if c != alternative_color])
        
        # Get features, pros, and cons
        features = random.sample(product['features'], min(3, len(product['features'])))
        pros = random.sample(product['pros'], min(2, len(product['pros'])))
        cons = random.sample(product['cons'], min(2, len(product['cons'])))
        
        # Get catchphrases
        catchphrase1 = random.choice(bot1['catchphrases'])
        catchphrase2 = random.choice(bot2['catchphrases'])
        catchphrase3 = random.choice(bot3['catchphrases'])
        
        # Generate conversation
        conversation = template['conversation']
        
        for i, line in enumerate(conversation):
            formatted_line = line.format(
                bot1_name=bot1['name'],
                bot2_name=bot2['name'],
                bot3_name=bot3['name'],
                bot1_emoji=bot1['emoji'],
                bot2_emoji=bot2['emoji'],
                bot3_emoji=bot3['emoji'],
                product_name=product['name'],
                product_category=product_category,
                feature1=features[0] if features else "features",
                feature2=features[1] if len(features) > 1 else "design",
                feature3=features[2] if len(features) > 2 else "performance",
                price=product['price'],
                pro1=pros[0] if pros else "quality",
                con1=cons[0] if cons else "price",
                alternative_product=alternative_product,
                color=color,
                alternative_color=alternative_color,
                catchphrase1=catchphrase1,
                catchphrase2=catchphrase2,
                catchphrase3=catchphrase3
            )
            
            # Extract bot name and message
            parts = formatted_line.split(': ', 1)
            if len(parts) == 2:
                bot_identifier, message_text = parts
                
                # Show typing indicator
                socketio.emit('bot_typing', {'is_typing': True})
                
                # Add product card to the last message in the conversation
                product_card = None
                if i == len(conversation) - 1:
                    product_card = {
                        'id': product['id'],
                        'name': product['name'],
                        'description': product['description'],
                        'price': product['price'],
                        'rating': product['rating'],
                        'image': product['image']
                    }
                
                # Wait for typing
                time.sleep(random.uniform(1.5, 3))
                socketio.emit('bot_typing', {'is_typing': False})
                
                message = {
                    'username': bot_identifier,
                    'message': message_text,
                    'timestamp': time.strftime('%H:%M:%S'),
                    'is_bot': True
                }
                
                if product_card:
                    message['product_card'] = product_card
                
                chat_messages.append(message)
                socketio.emit('message', message)
                
                # Add random delay between messages (2-5 seconds)
                time.sleep(random.uniform(2, 5))

def check_inactive_users():
    """Check for inactive users and have bots engage them in conversation"""
    while True:
        time.sleep(30)  # Check every 30 seconds
        current_time = time.time()
        
        for username, state in user_states.items():
            # If user has been inactive for 2-5 minutes (randomly chosen)
            inactive_threshold = random.randint(120, 300)
            if current_time - state["last_interaction"] > inactive_threshold:
                # Reset last interaction time to avoid multiple prompts
                state["last_interaction"] = current_time
                
                # Select a random bot to engage the user
                bot = random.choice(bot_personas)
                
                # Choose engagement type based on user state
                if state["conversation_stage"] == "greeting" or not state["asked_personal_question"]:
                    # Ask a personal question
                    question = random.choice(bot['casual_questions'])
                    message = f"Hey {username}, you've been quiet! {question}"
                    state["asked_personal_question"] = True
                elif state["mentioned_products"]:
                    # Follow up on a product they've mentioned
                    product_name = random.choice(list(state["mentioned_products"]))
                    product = next((p for p in products if p['name'] == product_name), None)
                    if product:
                        feature = random.choice(product['features'])
                        message = f"By the way {username}, I was wondering what you think about the {feature} on the {product_name}? It's one of my favorite features!"
                else:
                    # Suggest a random product
                    product = random.choice(products)
                    message = f"Hey {username}, I noticed you might be interested in our products. Have you checked out the {product['name']}? It's been really popular lately!"
                
                # Send the message
                bot_message = {
                    'username': f"{bot['name']} {bot['emoji']}",
                    'message': message,
                    'timestamp': time.strftime('%H:%M:%S'),
                    'is_bot': True
                }
                
                chat_messages.append(bot_message)
                socketio.emit('message', bot_message)

def trigger_bot_response_to_user(username, delay=5):
    """Trigger a bot response if no bot has responded to the user's message"""
    def delayed_response():
        time.sleep(delay)
        
        # Check if the last message was from the user
        if chat_messages and chat_messages[-1].get('username') == username:
            # Select a random bot
            bot = random.choice(bot_personas)
            
            # Generate a response asking for clarification
            responses = [
                f"Hey {username}, I noticed your message. Could you tell us more about what you're looking for?",
                f"{username}, I'm not sure I fully understood. Are you interested in a specific product or feature?",
                f"Sorry {username}, I might have missed something. What kind of tech are you interested in?",
                f"I'd love to help you, {username}! Could you clarify what you're looking for?",
                f"Let me make sure I understand correctly, {username}. Are you asking about our product lineup?"
            ]
            
            # Show typing indicator
            socketio.emit('bot_typing', {'is_typing': True})
            time.sleep(random.uniform(1.5, 2.5))
            socketio.emit('bot_typing', {'is_typing': False})
            
            # Send the response
            bot_message = {
                'username': f"{bot['name']} {bot['emoji']}",
                'message': random.choice(responses),
                'timestamp': time.strftime('%H:%M:%S'),
                'is_bot': True
            }
            
            chat_messages.append(bot_message)
            socketio.emit('message', bot_message)
            
            # Have another bot chime in
            time.sleep(random.uniform(2, 4))
            second_bot = random.choice([b for b in bot_personas if b['name'] != bot['name']])
            
            # Show typing indicator
            socketio.emit('bot_typing', {'is_typing': True})
            time.sleep(random.uniform(1.5, 2.5))
            socketio.emit('bot_typing', {'is_typing': False})
            
            # Generate a follow-up suggestion
            followups = [
                f"While we're waiting for {username}'s response, have you checked out our new {random.choice(products)['name']}?",
                f"I'm curious too, {username}! In the meantime, did you know our {random.choice(products)['name']} just got an update?",
                f"{bot['name']} asks good questions! {username}, we have several products that might interest you.",
                f"Just to add to what {bot['name']} said, we can help with recommendations if you tell us what you're looking for, {username}."
            ]
            
            followup_message = {
                'username': f"{second_bot['name']} {second_bot['emoji']}",
                'message': random.choice(followups),
                'timestamp': time.strftime('%H:%M:%S'),
                'is_bot': True
            }
            
            chat_messages.append(followup_message)
            socketio.emit('message', followup_message)
    
    # Start the delayed response thread
    response_thread = threading.Thread(target=delayed_response)
    response_thread.daemon = True
    response_thread.start()

if __name__ == '__main__':
    # Start bot conversation thread
    bot_thread = threading.Thread(target=generate_bot_conversation, daemon=True)
    bot_thread.start()
    
    # Start inactive user check thread
    inactive_thread = threading.Thread(target=check_inactive_users, daemon=True)
    inactive_thread.daemon = True
    inactive_thread.start()
    
    # Run the Flask app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
