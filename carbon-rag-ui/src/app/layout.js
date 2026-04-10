import './globals.scss';
import { Providers } from './providers';

export const metadata = {
  title: 'RAG Demo - AI on IBM Power',
  description: 'Retrieval Augmented Generation demo on IBM Power with the Carbon Design System',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}