import { Component, OnInit, ViewChild, OnDestroy } from '@angular/core';
import { IonSlides } from '@ionic/angular';
import { Router } from '@angular/router';
import { Preferences } from '@capacitor/preferences';
import { INTRO_KEY } from 'src/app/guards/intro.guard';
import { NavController } from '@ionic/angular';
@Component({
  selector: 'app-intro',
  templateUrl: './intro.page.html',
  styleUrls: ['./intro.page.scss'],
})
export class IntroPage implements OnInit, OnDestroy {
  @ViewChild(IonSlides, { static: true }) slides!: IonSlides;

  constructor(private router: Router,private navCtrl: NavController) {}
 
  ngOnInit() {
    this.addClickListener();
  }

  ngOnDestroy() {
    this.removeClickListener();
  }

  addClickListener() {
    const hamburgerMenu = document.querySelector(".hamburger-menu");
    const container = document.querySelector(".container");
    
    if (hamburgerMenu && container) {
      hamburgerMenu.addEventListener("click", this.toggleContainerClass);
    }
  }

  removeClickListener() {
    const hamburgerMenu = document.querySelector(".hamburger-menu");
    
    if (hamburgerMenu) {
      hamburgerMenu.removeEventListener("click", this.toggleContainerClass);
    }
  }

  toggleContainerClass() {
    const container = document.querySelector(".container");
    if (container) {
      container.classList.toggle("active");
    }
  }

  next() {
    this.slides.slideNext();
  }
  async navigateTo(tab: string) {
    try {
      console.log("Navigating to:", tab);
  
      let navigationPromise;
      switch(tab) {
        case 'record':
          navigationPromise = this.navCtrl.navigateRoot('/tabs/tab1');
          break;
        case 'history':
          // Bypass IntroGuard if navigating to history page
          navigationPromise = this.navCtrl.navigateForward('/tabs/tab2', { skipLocationChange: true });
          break;
        case 'dashboard':
          navigationPromise = this.navCtrl.navigateForward('/tabs/tab3');
          break;
        default:
          break;
      }
  
      if (navigationPromise) {
        console.log("Waiting for navigation to complete...");
        await navigationPromise;
        console.log("Navigation completed successfully.");
      } else {
        console.log("No navigation action specified.");
      }
    } catch (error) {
      console.error("Navigation error:", error);
      // Handle the error appropriately, such as showing a message to the user
    }
  }
  
  
  
  
  
}

