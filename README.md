# AI generated Aurora Borealis Art

Images are sourced from https://unsplash.com/search/photos/aurora-boreali

Note that there is no restriction on commercial use here, so free to train a GAN on in without any comeback!!



### Approach to getting images

Scrape the web page above and get the following:

1) Images are in a uniquely named div so need to work out how to scrape programmatically. 
All divs start with "_" so this might help!
1) Within the div, the image URLs are in \<srcset\>
1) The author's name is in \<alt\> so we can attribute later if need be




