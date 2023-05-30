## Translating the bot's interface
Copy `en.yaml` file and start translating. The file name must be the language code.



| Language     | Description                                                  |
| ------------ | ------------------------------------------------------------ |
| `code`       | JW language code. Example jw.org/en                                                            |
| `iso_code`   | A two-letter [ISO 639-1 language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). |
| `name`       | Language name in English                                                                       |
| `vernacular` | Language name in your own language.                                                            |



When translating, keep in mind html tags to style text. When you see `{}` or `{0}` it means that there is a variable, such as a command, a username, a language, etc. Keep them in their place so you don't throw an error.

If the translation is incomplete, the bot will use `en.yaml` file for the missing strings.