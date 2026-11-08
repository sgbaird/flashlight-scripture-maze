"""The scripture stories, one maze each, in play order.

Pictures come from "Old Testament Stories" (2022) on churchofjesuschrist.org, downloaded by
fetch_art.py into art/<slug>/01.jpg, 02.jpg, ... (page order). `card` is the picture shown
before and after the maze; `player` and `goal` are circular crops (picture number, centre x and
centre y as fractions of the picture's width and height, radius as a fraction of its height)
used for the walker and the goal; picture 1 of each chapter is a round portrait.
Without the pictures the activity draws simple figures instead.

Songs are from the Children's Songbook (churchofjesuschrist.org/media/music/songs/<slug>).
"""
from dataclasses import dataclass, field
from typing import Optional, Tuple

MUSIC = "https://www.churchofjesuschrist.org/media/music/songs/{slug}?lang=eng"
SONGBOOK = "https://www.churchofjesuschrist.org/media/music/collections/childrens-songbook?lang=eng"
STORY_URL = "https://www.churchofjesuschrist.org/study/manual/old-testament-stories-2022/{slug}?lang=eng"

Crop = Tuple[int, float, float, float]


@dataclass
class Story:
    slug: str                  # Old Testament Stories chapter
    title: str                 # shown on the story card
    short: str                 # one or two words for the map
    task: str                  # one line: what the walker does
    player_name: str
    goal_name: str
    ref: str                   # scripture reference
    ending: str                # one or two sentences shown at the end
    song: Tuple[str, str]      # (title, slug) in the Children's Songbook
    cfm: Optional[str] = None  # Come Follow Me week, if this is a current lesson
    items: Optional[Tuple[str, int, str]] = None  # (name, count, icon) to collect before the goal
    card: int = 1
    player: Crop = (1, 0.5, 0.5, 0.36)
    goal: Optional[Crop] = None
    goal_icon: Optional[str] = None  # drawn goal when there is no goal portrait: ark, tent, city (pictures.py)
    scenery: Optional[str] = None    # a few dim drawings along the paths: reeds, waves, lions, sheep, palms
    size: str = "medium"       # maze size: small, medium, large
    color: Tuple[int, int, int] = (90, 140, 230)  # fallback figure colour

    @property
    def song_url(self):
        return MUSIC.format(slug=self.song[1])

    @property
    def story_url(self):
        return STORY_URL.format(slug=self.slug)


STORIES = [
    Story(
        slug="daniel-and-his-friends",
        title="Daniel and His Friends",
        short="Daniel's Friends",
        task="Help Daniel and his friends find healthy food and water.",
        player_name="Daniel and his friends", goal_name="the king",
        ref="Daniel 1:8-20",
        ending="Daniel and his friends ate healthy food. The Lord blessed them, "
               "and they were wiser and healthier than everyone else.",
        song=("The Word of Wisdom", "the-word-of-wisdom"),
        cfm="Come Follow Me, November 9-15: Daniel 1-7",
        items=("vegetables", 4, "vegetable"), player=(1, 0.5, 0.42, 0.3), card=7, color=(60, 160, 90),
    ),
    Story(
        slug="daniel-and-the-kings-dream",
        title="Daniel and the King's Dream",
        short="King's Dream",
        task="King Nebuchadnezzar had a dream that no one could tell him. Daniel and his friends prayed, "
             "and God showed Daniel the dream. Help Daniel go to the king.",
        player_name="Daniel", goal_name="King Nebuchadnezzar",
        ref="Daniel 2:16-19, 27-28",
        ending="Daniel told the king his dream and what it meant. He said there is a God in heaven "
               "who reveals secrets.",
        song=("Search, Ponder, and Pray", "search-ponder-and-pray"),
        cfm="Come Follow Me, November 9-15: Daniel 1-7",
        player=(1, 0.5, 0.36, 0.24), card=7, goal=(3, 0.52, 0.3, 0.23), color=(200, 160, 70),
    ),
    Story(
        slug="shadrach-meshach-and-abed-nego",
        title="The Fiery Furnace",
        short="Fiery Furnace",
        task="Lead Shadrach, Meshach, and Abed-nego safely out of the fiery furnace "
             "to King Nebuchadnezzar.",
        player_name="Shadrach, Meshach, and Abed-nego", goal_name="King Nebuchadnezzar",
        ref="Daniel 3:16-28",
        ending="They would not worship the golden statue. The Lord protected them, "
               "and not even a hair on their heads was burned.",
        song=("Stand for the Right", "stand-for-the-right"),
        cfm="Come Follow Me, November 9-15: Daniel 1-7",
        player=(1, 0.51, 0.42, 0.29), card=5, goal=(2, 0.58, 0.56, 0.3), color=(230, 120, 40),
    ),
    Story(
        slug="daniel-and-the-lions-den",
        title="Daniel and the Lions' Den",
        short="Lions' Den",
        task="Daniel kept praying, so he was put in the lions' den. In the morning, "
             "help Daniel walk past the quiet lions to King Darius.",
        player_name="Daniel", goal_name="King Darius",
        ref="Daniel 6:10, 16-23",
        ending="Daniel kept praying to Heavenly Father. God sent His angel, "
               "and the lions did not hurt Daniel.",
        song=("A Child's Prayer", "a-childs-prayer"),
        cfm="Come Follow Me, November 9-15: Daniel 1-7",
        player=(1, 0.48, 0.35, 0.2), card=5, scenery="lions", color=(120, 90, 200),
    ),
    Story(
        slug="jeremiah-the-prophet",
        title="Jeremiah in the Dungeon",
        short="Jeremiah",
        task="Jeremiah was put in a muddy dungeon. Gather the ropes Ebed-melech let down "
             "and help Jeremiah climb out.",
        player_name="Jeremiah", goal_name="the way out",
        ref="Jeremiah 38:6-13",
        ending="Ebed-melech used ropes to lift Jeremiah out of the muddy dungeon. "
               "Jeremiah kept following the Lord even when things were hard.",
        song=("Follow the Prophet", "follow-the-prophet"),
        cfm="Come Follow Me, October 26 - November 1: Jeremiah",
        items=("ropes", 3, "rope"), player=(1, 0.48, 0.32, 0.25), card=4, color=(170, 110, 60),
    ),
    Story(
        slug="david-and-goliath",
        title="David's Five Smooth Stones",
        short="David",
        task="Help David pick five smooth stones from the brook.",
        player_name="David", goal_name="the Israelite camp",
        ref="1 Samuel 17:37-50",
        ending="David trusted the Lord. He was brave because he knew God would help him.",
        song=("I Will Be Valiant", "i-will-be-valiant"),
        items=("smooth stones", 5, "stone"), player=(1, 0.5, 0.56, 0.24), card=7, goal_icon="tent", scenery="sheep", color=(90, 140, 230),
    ),
    Story(
        slug="noah-and-his-family",
        title="Noah's Ark",
        short="Noah",
        task="Help Noah gather the animals and lead them into the ark.",
        player_name="Noah", goal_name="the ark",
        ref="Genesis 6:13-22; 7:1-16",
        ending="Noah followed the Lord and built the ark. His family and the animals were safe.",
        song=("Follow the Prophet", "follow-the-prophet"),
        items=("animals", 4, "animal"), player=(1, 0.56, 0.42, 0.27), card=5, goal_icon="ark", color=(150, 110, 70),
    ),
    Story(
        slug="baby-moses",
        title="Baby Moses",
        short="Baby Moses",
        task="Moses' mother hid him in a basket by the river, and his sister Miriam watched over him. "
             "Help them reach Pharaoh's daughter.",
        player_name="Moses and his mother", goal_name="Pharaoh's daughter",
        ref="Exodus 2:1-10",
        ending="Miriam watched over her baby brother. Pharaoh's daughter found Moses "
               "and kept him safe.",
        song=("I Am a Child of God", "i-am-a-child-of-god"),
        size="small", player=(1, 0.56, 0.4, 0.28), card=5, goal=(6, 0.7, 0.3, 0.2), scenery="reeds", color=(220, 110, 160),
    ),
    Story(
        slug="the-passover",
        title="Through the Red Sea",
        short="Red Sea",
        task="Lead the Israelites through the Red Sea on dry ground.",
        player_name="Moses", goal_name="the other side",
        ref="Exodus 14:13-22",
        ending="The Lord parted the Red Sea, and the Israelites walked through on dry ground.",
        song=("I Will Follow God's Plan", "i-will-follow-gods-plan"),
        size="large", player=(1, 0.47, 0.42, 0.3), card=11, scenery="waves", color=(70, 120, 200),
    ),
    Story(
        slug="ruth-and-naomi",
        title="Ruth Gathers Grain",
        short="Ruth",
        task="Help Ruth gather grain in Boaz's field for Naomi.",
        player_name="Ruth", goal_name="Naomi",
        ref="Ruth 2:2-18",
        ending="Ruth loved Naomi and took care of her. Boaz was kind and let Ruth gather grain.",
        song=("Love One Another", "love-one-another"),
        items=("grain", 5, "grain"), player=(1, 0.52, 0.42, 0.3), card=5, goal=(3, 0.38, 0.44, 0.16), color=(200, 150, 60),
    ),
    Story(
        slug="queen-esther",
        title="Queen Esther",
        short="Esther",
        task="Help Queen Esther go to the king to save her people.",
        player_name="Esther", goal_name="the king",
        ref="Esther 4:14-16; 5:1-3",
        ending="Esther fasted and was brave. She went to the king and saved her people.",
        song=("Choose the Right", "choose-the-right"),
        size="large", player=(1, 0.48, 0.42, 0.32), card=10, goal=(10, 0.13, 0.36, 0.16), color=(150, 80, 190),
    ),
    Story(
        slug="jonah-the-prophet",
        title="Jonah Goes to Nineveh",
        short="Jonah",
        task="Help Jonah go to Nineveh to teach the people.",
        player_name="Jonah", goal_name="Nineveh",
        ref="Jonah 3:1-10",
        ending="Jonah obeyed the second time. The people of Nineveh listened and repented.",
        song=("Keep the Commandments", "keep-the-commandments"),
        player=(1, 0.5, 0.4, 0.3), card=9, goal_icon="city", scenery="palms", color=(60, 150, 170),
    ),
]
