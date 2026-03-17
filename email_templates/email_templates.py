def build_signed_copy_email(row: dict, token: str) -> str:
    first_name = row.get("first_name") or ""
    greeting = f"Dear {first_name}," if first_name else "Hello,"
    
    brand_blue = "#00008f"
    text_black = "#000000"
    light_grey = "#f2f2f2"
    logo_url = "https://cdn.shopify.com/s/files/1/0297/5046/0549/files/KitArt_LetLogo.png?v=1709610671"
    
    base_url = "https://www.kitchenartsandletters.com/pages/signed-copy-response"

    def link(r):
        return f"{base_url}?t={token}&r={r}"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
    </head>
    <body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
      <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <tr>
          <td align="center" style="padding: 20px 0 40px 0;">
            <a href="https://www.kitchenartsandletters.com">
              <img src="{logo_url}" alt="Kitchen Arts & Letters" width="220" style="display: block; border: 0; height: auto; outline: none; text-decoration: none;">
            </a>
          </td>
        </tr>

        <tr>
          <td style="color: {text_black}; font-size: 16px; line-height: 1.6;">
            
            <p style="margin-top: 0;">{greeting}</p>

            <p>
              When you placed your preorder, you were excited about this book. And we were excited to get it to you. 
              But I've been following the recent news about co-author René Redzepi, and I don’t feel right sending 
              out copies without checking in first.
            </p>

            <p>
              I'd rather know if your feelings about the book have changed than have you receive something you wish 
              you hadn't ordered. That's why I’m writing to everyone who preordered.
            </p>

            <p style="font-weight: bold; margin-top: 25px;">Please choose one of the options below:</p>

            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 25px 0;">
              <tr>
                <td style="padding-bottom: 12px;">
                  <a href="{link('keep')}" style="display: block; background-color: {brand_blue}; color: #ffffff; padding: 14px 20px; text-decoration: none; text-align: center; border-radius: 4px; font-weight: bold; font-size: 15px;">
                    Keep your order as-is for a signed copy (which will come to us already signed)
                  </a>
                </td>
              </tr>
              <tr>
                <td style="padding-bottom: 12px;">
                  <a href="{link('unsigned')}" style="display: block; background-color: {brand_blue}; color: #ffffff; padding: 14px 20px; text-decoration: none; text-align: center; border-radius: 4px; font-weight: bold; font-size: 15px;">
                    Switch to an unsigned copy
                  </a>
                </td>
              </tr>
              <tr>
                <td style="padding-bottom: 12px;">
                  <a href="{link('cancel')}" style="display: block; background-color: {brand_blue}; color: #ffffff; padding: 14px 20px; text-decoration: none; text-align: center; border-radius: 4px; font-weight: bold; font-size: 15px;">
                    Cancel your order for a full refund of the book and any shipping costs
                  </a>
                </td>
              </tr>
            </table>

            <p style="font-size: 14px; color: #666666; font-style: italic; margin-top: 30px;">
              There's no wrong answer. If you cancel, you'll receive a complete refund and you're welcome to keep any rewards points you earned on the preorder.
            </p>

            <p style="font-size: 14px; color: #666666; font-style: italic; margin-top: 15px;">
              If we don't hear from you by midnight on Friday, March 20, we'll take that as a sign you'd like to proceed with your signed copy and fulfill your order accordingly.
            </p>

            <p style="margin-bottom: 0;">
              Thank you for being a Kitchen Arts & Letters customer. I don't take that for granted.
            </p>

          </td>
        </tr>
        
        <tr>
          <td align="center" style="padding-top: 40px; border-top: 1px solid #f2f2f2; margin-top: 20px;">
            <p style="font-size: 12px; color: #999999;">
              Kitchen Arts & Letters | 1435 Lexington Avenue, New York, NY 10128
            </p>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """