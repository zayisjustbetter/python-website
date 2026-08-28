<HCaptcha />

const [captchaToken, setCaptchaToken] = useState(),

<HCaptcha
  sitekey="cc9842f4-787e-471c-970e-29a4718462a0"
  onVerify={(token) => {
    setCaptchaToken(token)
  }}
/>