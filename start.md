- Install miniconda https://docs.conda.io/projects/miniconda/en/latest/index.html#quick-command-line-install

- git clone https://github.com/vbastianpc/nwt-signs-bot
- cd nwt-signs-bot/
- conda env create -f environment.yml
- conda activate nwt-bot

- create .env
- python start_config.yml
- python start.py

1. Install miniconda. Follow these steps (Quick command line install > Linux)


2. Clone repository and change directory
```bash
git clone https://github.com/vbastianpc/nwt-signs-bot
```


3. Change directory.
```bash
cd nwt-signs-bot
```


4. Install prerequisites.
```bash
conda env create -f environment.yml
```


5. Activate environment
```bash
conda activate nwt-bot
```


6. Create environment variables file
```bash
nano .env
```
and write the sensitive text that I will send you internally.


7. Start configuration.
```bash
python start_config.py
```


8. Run the bot.
```bash
python start.py
```

or
```bash
nohup python start.py > log.log &
```

to run the bot when you close terminal