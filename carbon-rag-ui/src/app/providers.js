'use client';

import Header from '../components/Header/Header';
import { Content, Theme } from '@carbon/react';

export function Providers({ children }) {
  return (
<div>
  <Theme theme="g100">
    <Header />
  </Theme>
  <Content>{children}</Content>
</div>
  );
}
