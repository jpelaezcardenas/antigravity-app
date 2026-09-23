import type { ReactNode } from "react";
import Script from "next/script";

const META_PIXEL_ID = "1754537042427579";

export default function RentaNaturalLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="min-h-screen flex flex-col text-on-surface"
      style={{
        backgroundColor: "#020617",
        backgroundImage:
          "radial-gradient(circle at 15% 10%, rgba(45, 212, 191, 0.08) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(139, 92, 246, 0.06) 0%, transparent 50%)",
      }}
    >
      <Script id="meta-pixel-renta-natural" strategy="afterInteractive">
        {`
          !function(f,b,e,v,n,t,s)
          {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
          n.callMethod.apply(n,arguments):n.queue.push(arguments)};
          if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
          n.queue=[];t=b.createElement(e);t.async=!0;
          t.src=v;s=b.getElementsByTagName(e)[0];
          s.parentNode.insertBefore(t,s)}(window, document,'script',
          'https://connect.facebook.net/en_US/fbevents.js');
          fbq('init', '${META_PIXEL_ID}');
          fbq('track', 'PageView');
        `}
      </Script>
      <noscript>
        <img
          height="1"
          width="1"
          style={{ display: "none" }}
          src={`https://www.facebook.com/tr?id=${META_PIXEL_ID}&ev=PageView&noscript=1`}
          alt=""
        />
      </noscript>
      {children}
    </div>
  );
}
