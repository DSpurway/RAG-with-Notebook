'use client';
import {
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Tabs,
  Tab,
  TabList,
  TabPanels,
  TabPanel,
  Grid,
  Column,
} from '@carbon/react';
import Image from 'next/image';

export default function LandingPage() {
  return (
    <Grid className="landing-page" fullWidth>
      <Column lg={16} md={8} sm={4} className="landing-page__banner">
        <Breadcrumb noTrailingSlash aria-label="Page navigation">
          <BreadcrumbItem>
            <a href="/">Getting started</a>
          </BreadcrumbItem>
        </Breadcrumb>
        <h1 className="landing-page__heading">RAG Demo: GenAI on IBM Power</h1>
      </Column>
      <Column lg={16} md={8} sm={4} className="landing-page__r2">
        <Tabs defaultSelectedIndex={0}>
          <TabList className="tabs-group" aria-label="Tab navigation">
            <Tab>About</Tab>
            <Tab>Secure</Tab>
            <Tab>Flexible</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column md={4} lg={7} sm={4} className="landing-page__tab-content">
                  <h3 className="landing-page__subheading">Retrieval Augmented Generation (RAG)</h3>
                  <p className="landing-page__p">
                    This demo showcases Retrieval Augmented Generation (RAG) running on IBM Power.
                    RAG enhances Large Language Models by providing them with relevant context from
                    your documents, enabling accurate answers without retraining. Experience how
                    IBM Power's Matrix Math Accelerator (MMA) delivers efficient AI inference
                    while keeping your data secure within your infrastructure.
                  </p>
                  <Button href="/rag">Try the RAG Demo</Button>
                </Column>
                <Column md={4} lg={{ span: 8, offset: 7 }} sm={4}>
                  <Image
                    className="landing-page__illo"
                    src="https://newsroom.ibm.com/image/Power11-Launch-SocialKit_Banner.png"
                    alt="IBM Power based on Power11 illustration"
                    width={604}
                    height={498}
                  />
                </Column>
              </Grid>
            </TabPanel>
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4} className="landing-page__tab-content">
                  <p className="landing-page__p">
                    Your data can remain safe and secure inside IBM Power, without needing
                    to leave your control. IBM Power also has orders of magnitude fewer
                    security vulnerabilities in the virtualisation that is in the heart of
                    every IBM Power server, lowering the surface area that can be attacked
                    by bad actors.
                  </p>
                </Column>
              </Grid>
            </TabPanel>
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4} className="landing-page__tab-content">
                  <p className="landing-page__p">
                    This demo uses TinyLlama and Granite models running on IBM Power, downloaded
                    from Hugging Face. You can easily swap models to suit your use case - whether
                    Mistral, Llama, or others. Deploy different models in separate virtual servers
                    without GPU constraints. Choose the right model for each workload, maintaining
                    flexibility and control over your AI infrastructure.
                  </p>
                </Column>
              </Grid>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Column>
      <Column lg={16} md={8} sm={4} className="landing-page__r3">
        <Grid>
          <Column lg={4} md={2} sm={4}>
            <h3 className="landing-page__label">The Principles</h3>
          </Column>
          <Column
            lg={{ start: 5, span: 3 }}
            md={{ start: 3, span: 6 }}
            sm={4}
            className="landing-page__title"
            style={{ textAlign: 'center' }}>
            <h4>💾 Data Locality</h4>
            <div>Run GenAI Models where your data lives</div>
          </Column>
          <Column
            lg={{ start: 9, span: 3 }}
            md={{ start: 3, span: 6 }}
            sm={4}
            className="landing-page__title"
            style={{ textAlign: 'center' }}>
            <h4>🔒 Security</h4>
            <div>Ensure data sovereignty</div>
          </Column>
          <Column
            lg={{ start: 13, span: 3 }}
            md={{ start: 3, span: 6 }}
            sm={4}
            className="landing-page__title"
            style={{ textAlign: 'center' }}>
            <h4>⚡ Reliability</h4>
            <div>Legendary reliability</div>
          </Column>
        </Grid>
      </Column>
    </Grid>
  );
}

// Made with Bob
