import React from 'react';
import axios from "axios";
import './App.css';

type ResponseSelectorSectionProps = {};
type ResponseSelectorSectionState = {
  selectedButtons: Array<string>;
}

const BASE_URL = "http://192.168.1.220:4000";
class ResponseSelectorSection extends 
React.Component<ResponseSelectorSectionProps, ResponseSelectorSectionState> {
  constructor(props:ResponseSelectorSectionState) {
    super(props);
    this.state = {
      selectedButtons: []
    };
  }

  public render() {
    const rewardButtons = [
      "Reward"
    ];
    const greetings = [
      "Hey",
      "Hello",
      "Hi"
    ];
    const people = [
      "Sam",
      "Mom",
      "Chantal",
      "Pinot",
      "Grandpa",
      "Grandma",
      "Grigio"
    ];
    const sayings = [
      "My name is",
      "How are you?",
    ];
    const rewardSection = rewardButtons.map(text => {
      return (
        <button onClick={this.onRewardPress.bind(this)}>{text}</button>
      );
    });
    const greetingSection = greetings.map(text => {
      return (
        <button onClick={this.onBtnPress.bind(this)}>{text}</button>
      )
    });
    const peopleSection = people.map(text => {
      return (
        <button onClick={this.onBtnPress.bind(this)}>{text}</button>
      )
    });
    const sayingSection = sayings.map(text => {
      return (
        <button onClick={this.onBtnPress.bind(this)}>{text}</button>
      )
    });
    return (
      <div>
        <div>{rewardSection}</div>
        <div>{greetingSection}</div>
        <div>{peopleSection}</div>
        <div>{sayingSection}</div>
      </div>
    )
  }

  private async onBtnPress(evt: React.MouseEvent<HTMLButtonElement>) {
    const text = evt.currentTarget.textContent;
    console.log("PRESSED:", text);
    const resp = await axios.put(BASE_URL + "/control", {
      speak: text,
    });
    console.log("Press resp:", resp);
  }

  private onRewardPress(evt: React.MouseEvent<HTMLButtonElement>) {
    console.log("Reward pressed");
  }
}


type Props = {};
type State = {};
class App extends React.Component<Props, State> {
  constructor(props:Props) {
    super(props);
  }

  public render() {
    
    return (
      <div className="App">
        <body>
          <div>
            <ResponseSelectorSection/>
          </div>
        </body>
      </div>
    );
  }
}

export default App;
